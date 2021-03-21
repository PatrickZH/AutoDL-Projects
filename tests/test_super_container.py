#####################################################
# Copyright (c) Xuanyi Dong [GitHub D-X-Y], 2021.03 #
#####################################################
# pytest ./tests/test_super_container.py -s         #
#####################################################
import sys, random
import unittest
import pytest
from pathlib import Path

lib_dir = (Path(__file__).parent / ".." / "lib").resolve()
print("library path: {:}".format(lib_dir))
if str(lib_dir) not in sys.path:
    sys.path.insert(0, str(lib_dir))

import torch
from xlayers import super_core
import spaces


"""Test the super container layers."""


def _internal_func(inputs, model):
    outputs = model(inputs)
    abstract_space = model.abstract_search_space
    print(
        "The abstract search space for SuperAttention is:\n{:}".format(abstract_space)
    )
    abstract_space.clean_last()
    abstract_child = abstract_space.random(reuse_last=True)
    print("The abstract child program is:\n{:}".format(abstract_child))
    model.set_super_run_type(super_core.SuperRunMode.Candidate)
    model.apply_candidate(abstract_child)
    outputs = model(inputs)
    return abstract_child, outputs


def _create_stel(input_dim, output_dim):
    return super_core.SuperTransformerEncoderLayer(
        input_dim,
        output_dim,
        num_heads=spaces.Categorical(2, 4, 6),
        mlp_hidden_multiplier=spaces.Categorical(1, 2, 4),
    )


@pytest.mark.parametrize("batch", (1, 2, 4))
@pytest.mark.parametrize("seq_dim", (1, 10, 30))
@pytest.mark.parametrize("input_dim", (6, 12, 24, 27))
def test_super_sequential(batch, seq_dim, input_dim):
    out1_dim = spaces.Categorical(12, 24, 36)
    out2_dim = spaces.Categorical(24, 36, 48)
    out3_dim = spaces.Categorical(36, 72, 100)
    layer1 = _create_stel(input_dim, out1_dim)
    layer2 = _create_stel(out1_dim, out2_dim)
    layer3 = _create_stel(out2_dim, out3_dim)
    model = super_core.SuperSequential(layer1, layer2, layer3)
    print(model)
    model.apply_verbose(True)
    inputs = torch.rand(batch, seq_dim, input_dim)
    abstract_child, outputs = _internal_func(inputs, model)
    output_shape = (
        batch,
        seq_dim,
        out3_dim.abstract(reuse_last=True).random(reuse_last=True).value,
    )
    assert tuple(outputs.shape) == output_shape