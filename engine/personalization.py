"""Speaker-personalized fine-tuning for the Auto-AVSR model."""

import math

import torch

from lightning import ModelModule


class PersonalizationModelModule(ModelModule):
    """Fine-tunes a bounded subset of the visual speech model.

    The default strategy keeps the video frontend and most of the Conformer
    frozen. This is intentionally conservative for a few hundred personal
    recordings: it preserves general lip-reading features while adapting the
    last temporal blocks and both output heads to one speaker.
    """

    VALID_STRATEGIES = {"decoder", "encoder-decoder", "full"}

    def __init__(self, args):
        super().__init__(args)
        self.finetune_strategy = getattr(args, "finetune_strategy", "encoder-decoder")
        self.unfreeze_encoder_layers = int(
            getattr(args, "unfreeze_encoder_layers", 2)
        )
        self._configure_trainable_parameters()

    def _configure_trainable_parameters(self):
        if self.finetune_strategy not in self.VALID_STRATEGIES:
            raise ValueError(
                f"Unknown fine-tune strategy: {self.finetune_strategy}. "
                f"Choose one of {sorted(self.VALID_STRATEGIES)}."
            )

        if self.finetune_strategy == "full":
            for parameter in self.model.parameters():
                parameter.requires_grad = True
            return

        for parameter in self.model.parameters():
            parameter.requires_grad = False

        # Both decoding paths contribute to the joint CTC/attention loss.
        for module in (self.model.decoder, self.model.ctc):
            for parameter in module.parameters():
                parameter.requires_grad = True

        if self.finetune_strategy == "encoder-decoder":
            layers = list(self.model.encoder.encoders)
            if not 1 <= self.unfreeze_encoder_layers <= len(layers):
                raise ValueError(
                    "unfreeze_encoder_layers must be between 1 and "
                    f"{len(layers)}"
                )
            for parameter in self.model.proj_encoder.parameters():
                parameter.requires_grad = True
            for layer in layers[-self.unfreeze_encoder_layers :]:
                for parameter in layer.parameters():
                    parameter.requires_grad = True

    def on_train_epoch_start(self):
        # Lightning calls train() recursively each epoch. Put frozen modules
        # back in eval mode so BatchNorm statistics and dropout do not drift.
        if self.finetune_strategy == "full":
            return

        self.model.frontend.eval()
        if self.finetune_strategy == "decoder":
            self.model.proj_encoder.eval()
            self.model.encoder.eval()
            return

        layers = list(self.model.encoder.encoders)
        if hasattr(self.model.encoder, "embed"):
            self.model.encoder.embed.eval()
        for layer in layers[: -self.unfreeze_encoder_layers]:
            layer.eval()

    @property
    def parameter_counts(self):
        total = sum(parameter.numel() for parameter in self.model.parameters())
        trainable = sum(
            parameter.numel()
            for parameter in self.model.parameters()
            if parameter.requires_grad
        )
        return {"total": total, "trainable": trainable}

    def configure_optimizers(self):
        trainable_parameters = [
            parameter
            for parameter in self.model.parameters()
            if parameter.requires_grad
        ]
        if not trainable_parameters:
            raise RuntimeError(
                "The selected fine-tune strategy has no trainable parameters"
            )

        optimizer = torch.optim.AdamW(
            trainable_parameters,
            lr=self.args.lr,
            weight_decay=self.args.weight_decay,
            betas=(0.9, 0.98),
        )
        steps_per_epoch = max(
            1,
            int(
                len(self.trainer.datamodule.train_dataloader())
                / max(1, self.trainer.num_devices)
                / max(1, self.trainer.num_nodes)
            ),
        )
        total_steps = max(1, self.args.max_epochs * steps_per_epoch)
        warmup_steps = min(
            total_steps,
            max(0, self.args.warmup_epochs * steps_per_epoch),
        )

        def lr_factor(step):
            if warmup_steps and step < warmup_steps:
                return (step + 1) / warmup_steps
            decay_steps = max(1, total_steps - warmup_steps)
            progress = min(1.0, max(0.0, (step - warmup_steps) / decay_steps))
            return 0.5 * (1.0 + math.cos(math.pi * progress))

        scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_factor)
        return [optimizer], [{"scheduler": scheduler, "interval": "step"}]
