#!/usr/bin/env python3

"""
@author: l00511303
@since: 
"""

import math

from torch.optim import Optimizer
from torch.optim.lr_scheduler import LambdaLR


class CosineWarmupAnnealingLR(LambdaLR):

    def __init__(self,
                 optimizer: Optimizer,
                 num_loops,
                 max_a=1.0,
                 min_a=0.0,
                 warmup_percentage=0.01,
                 warmup_pow=None,
                 annealing_pow=2.0,
                 last_epoch=-1):
        assert num_loops > 0
        self._num_loops = num_loops
        assert max_a > min_a
        self._max_a = max_a
        self._min_a = min_a
        assert 0.0 < warmup_percentage < 1.0
        self._warmup_proportion = warmup_percentage
        self._warmup_pow = warmup_pow
        self._annealing_pow = annealing_pow

        self._warmup_loops = int(self._num_loops * self._warmup_proportion)
        self._annealing_loops = self._num_loops - self._warmup_loops
        super(CosineWarmupAnnealingLR, self).__init__(
            optimizer=optimizer,
            lr_lambda=self._lr_lambda,
            last_epoch=last_epoch
        )

    def _lr_lambda(self, i: int) -> float:
        if i < self._warmup_loops:
            i = self._warmup_loops - 1 - i
            value = math.cos(i / self._warmup_loops * math.pi)
            value = 0.5 * (value + 1.0)
            if self._warmup_pow is not None:
                value = math.pow(value, self._warmup_pow)
            value = (self._max_a - self._min_a) * value + self._min_a
        else:
            i = i - self._warmup_loops
            value = math.cos(i / self._annealing_loops * math.pi)
            value = 0.5 * (value + 1.0)
            if self._annealing_pow is not None:
                value = math.pow(value, self._annealing_pow)
            value = (self._max_a - self._min_a) * value + self._min_a
        return value
