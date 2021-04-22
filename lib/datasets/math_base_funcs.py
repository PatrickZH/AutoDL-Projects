#####################################################
# Copyright (c) Xuanyi Dong [GitHub D-X-Y], 2021.03 #
#####################################################
import math
import abc
import copy
import numpy as np
from typing import Optional
import torch
import torch.utils.data as data


class FitFunc(abc.ABC):
    """The fit function that outputs f(x) = a * x^2 + b * x + c."""

    def __init__(self, freedom: int, list_of_points=None):
        self._params = dict()
        for i in range(freedom):
            self._params[i] = None
        self._freedom = freedom
        if list_of_points is not None:
            self.fit(list_of_points)

    def set(self, _params):
        self._params = copy.deepcopy(_params)

    def check_valid(self):
        for key, value in self._params.items():
            if value is None:
                raise ValueError("The {:} is None".format(key))

    @abc.abstractmethod
    def __call__(self, x):
        raise NotImplementedError

    @abc.abstractmethod
    def _getitem(self, x):
        raise NotImplementedError

    def fit(
        self,
        list_of_points,
        max_iter=900,
        lr_max=1.0,
        verbose=False,
    ):
        with torch.no_grad():
            data = torch.Tensor(list_of_points).type(torch.float32)
            assert data.ndim == 2 and data.size(1) == 2, "Invalid shape : {:}".format(
                data.shape
            )
            x, y = data[:, 0], data[:, 1]
        weights = torch.nn.Parameter(torch.Tensor(self._freedom))
        torch.nn.init.normal_(weights, mean=0.0, std=1.0)
        optimizer = torch.optim.Adam([weights], lr=lr_max, amsgrad=True)
        lr_scheduler = torch.optim.lr_scheduler.MultiStepLR(
            optimizer,
            milestones=[
                int(max_iter * 0.25),
                int(max_iter * 0.5),
                int(max_iter * 0.75),
            ],
            gamma=0.1,
        )
        if verbose:
            print("The optimizer: {:}".format(optimizer))

        best_loss = None
        for _iter in range(max_iter):
            y_hat = self._getitem(x, weights)
            loss = torch.mean(torch.abs(y - y_hat))
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            lr_scheduler.step()
            if verbose:
                print(
                    "In the fit, loss at the {:02d}/{:02d}-th iter is {:}".format(
                        _iter, max_iter, loss.item()
                    )
                )
            # Update the params
            if best_loss is None or best_loss > loss.item():
                best_loss = loss.item()
                for i in range(self._freedom):
                    self._params[i] = weights[i].item()

    def __repr__(self):
        return "{name}(freedom={freedom})".format(
            name=self.__class__.__name__, freedom=freedom
        )


class QuadraticFunc(FitFunc):
    """The quadratic function that outputs f(x) = a * x^2 + b * x + c."""

    def __init__(self, list_of_points=None):
        super(QuadraticFunc, self).__init__(3, list_of_points)

    def __call__(self, x):
        self.check_valid()
        return self._params[0] * x * x + self._params[1] * x + self._params[2]

    def _getitem(self, x, weights):
        return weights[0] * x * x + weights[1] * x + weights[2]

    def __repr__(self):
        return "{name}(y = {a} * x^2 + {b} * x + {c})".format(
            name=self.__class__.__name__,
            a=self._params[0],
            b=self._params[1],
            c=self._params[2],
        )


class CubicFunc(FitFunc):
    """The cubic function that outputs f(x) = a * x^3 + b * x^2 + c * x + d."""

    def __init__(self, list_of_points=None):
        super(CubicFunc, self).__init__(4, list_of_points)

    def __call__(self, x):
        self.check_valid()
        return (
            self._params[0] * x ** 3
            + self._params[1] * x ** 2
            + self._params[2] * x
            + self._params[3]
        )

    def _getitem(self, x, weights):
        return weights[0] * x ** 3 + weights[1] * x ** 2 + weights[2] * x + weights[3]

    def __repr__(self):
        return "{name}(y = {a} * x^3 + {b} * x^2 + {c} * x + {d})".format(
            name=self.__class__.__name__,
            a=self._params[0],
            b=self._params[1],
            c=self._params[2],
            d=self._params[3],
        )


class QuarticFunc(FitFunc):
    """The quartic function that outputs f(x) = a * x^4 + b * x^3 + c * x^2 + d * x + e."""

    def __init__(self, list_of_points=None):
        super(QuarticFunc, self).__init__(5, list_of_points)

    def __call__(self, x):
        self.check_valid()
        return (
            self._params[0] * x ** 4
            + self._params[1] * x ** 3
            + self._params[2] * x ** 2
            + self._params[3] * x
            + self._params[4]
        )

    def _getitem(self, x, weights):
        return (
            weights[0] * x ** 4
            + weights[1] * x ** 3
            + weights[2] * x ** 2
            + weights[3] * x
            + weights[4]
        )

    def __repr__(self):
        return "{name}(y = {a} * x^4 + {b} * x^3 + {c} * x^2 + {d} * x + {e})".format(
            name=self.__class__.__name__,
            a=self._params[0],
            b=self._params[1],
            c=self._params[2],
            d=self._params[3],
            e=self._params[3],
        )


class DynamicQuadraticFunc(FitFunc):
    """The dynamic quadratic function that outputs f(x) = a * x^2 + b * x + c."""

    def __init__(self, list_of_points=None):
        super(DynamicQuadraticFunc, self).__init__(3, list_of_points)
        self._timestamp = None

    def __call__(self, x):
        self.check_valid()
        a = self._params[0][self._timestamp]
        b = self._params[1][self._timestamp]
        c = self._params[2][self._timestamp]
        convert_fn = lambda x: x[-1] if isinstance(x, (tuple, list)) else x
        a, b, c = convert_fn(a), convert_fn(b), convert_fn(c)
        return a * x * x + b * x + c

    def _getitem(self, x, weights):
        raise NotImplementedError

    def set_timestamp(self, timestamp):
        self._timestamp = timestamp

    def __repr__(self):
        return "{name}(y = {a} * x^2 + {b} * x + {c})".format(
            name=self.__class__.__name__,
            a=self._params[0],
            b=self._params[1],
            c=self._params[2],
        )
