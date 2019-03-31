import tensorflow as tf
import numpy as np
import argparse
import functools
import glob
import hooks
from param import Param
from dataset import cifar10_input_fn
from model import Classifier
from network import ResNet

parser = argparse.ArgumentParser()
parser.add_argument("--model_dir", type=str, default="cifar10_resnet_model")
parser.add_argument('--filenames', type=str, default="cifar-10-batches-py/data_batch*")
parser.add_argument("--batch_size", type=int, default=64)
parser.add_argument("--num_epochs", type=int, default=200)
parser.add_argument("--max_steps", type=int, default=None)
parser.add_argument("--steps", type=int, default=None)
parser.add_argument('--train', action="store_true")
parser.add_argument('--eval', action="store_true")
args = parser.parse_args()

tf.logging.set_verbosity(tf.logging.INFO)


if __name__ == "__main__":

    estimator = tf.estimator.Estimator(
        model_fn=Classifier(
            network=ResNet(
                conv_param=Param(filters=16, kernel_size=[3, 3], strides=[1, 1]),
                pool_param=None,
                residual_params=[
                    Param(filters=32, strides=[1, 1], blocks=3),
                    Param(filters=64, strides=[2, 2], blocks=3),
                    Param(filters=128, strides=[2, 2], blocks=3),
                ],
                num_classes=10,
                apply_weight_standardization=True
            ),
            params=Param(
                weight_decay=2e-4,
                learning_rate_fn=lambda global_step: tf.train.piecewise_constant(
                    x=global_step,
                    boundaries=[50000 * num_epochs // args.batch_size for num_epochs in [100, 150, 200]],
                    values=[0.1 * decay_rate for decay_rate in [1.0, 0.1, 0.01, 0.001]]
                ),
                momentum=0.9
            )
        ),
        model_dir=args.model_dir,
        config=tf.estimator.RunConfig(
            save_summary_steps=100,
            save_checkpoints_steps=1000
        )
    )

    if args.train:

        estimator.train(
            input_fn=functools.partial(
                cifar10_input_fn,
                filenames=glob.glob(args.train_filenames),
                batch_size=args.batch_size,
                num_epochs=args.num_epochs if args.train else 1,
                shuffle=True if args.train else False,
            ),
            steps=args.steps,
            max_steps=args.max_steps
        )

    if args.eval:

        print("==================================================")
        tf.logging.info(estimator.evaluate(
            input_fn=functools.partial(
                cifar10_input_fn,
                filenames=glob.glob(args.filenames),
                batch_size=args.batch_size,
                num_epochs=1,
                shuffle=False,
            ),
            steps=args.steps
        ))
        print("==================================================")
