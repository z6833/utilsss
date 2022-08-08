# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import torch
import torch.nn.functional as F
from torch.optim.lr_scheduler import LambdaLR


def Conv1D(in_channels, out_channels, kernel_size=3, stride=1, padding=1):
    return torch.nn.Sequential(
        torch.nn.Conv1d(in_channels, out_channels, kernel_size=kernel_size, stride=stride, padding=padding, bias=True),
        torch.nn.BatchNorm1d(out_channels),
        torch.nn.LeakyReLU())


class ResidualBlock(torch.nn.Module):
    def __init__(self, in_channels):
        super(ResidualBlock, self).__init__()

        reduced_channels = int(in_channels / 2)

        self.layer1 = Conv1D(in_channels, reduced_channels, kernel_size=1, padding=0)
        self.layer2 = Conv1D(reduced_channels, in_channels)

    def forward(self, x):
        residual = x
        out = self.layer1(x)
        out = self.layer2(out)
        out += residual
        return out


# Attention
class yannet(torch.nn.Module):
    def __init__(self):
        super(yannet, self).__init__()
        self.name = 'yannet'
        self.conv1 = Conv1D(2, 32)

        self.conv2 = Conv1D(32, 64, stride=2)
        self.residual_block2 = self.make_layer(in_channels=64, num_blocks=2)

        self.conv3 = Conv1D(64, 128, stride=2)
        self.residual_block3 = self.make_layer(in_channels=128, num_blocks=2)

        self.fc1 = torch.nn.Linear(128 * 20, 100)
        self.fc2 = torch.nn.Linear(100, 1)

    def forward(self, query, key):
        # key
        # (B, T)->(B, 1, T), T=78
        key = torch.unsqueeze(key, 1)
        query = torch.unsqueeze(query, 1)

        x = torch.cat((query, key), 1)

        # (B,2,78)->(B,32,78)
        x = self.conv1(x)

        # (B,32,78)->(B,64,39)
        x = self.conv2(x)
        x = self.residual_block2(x)

        # (B,64,39)->(B,128,20)
        x = self.conv3(x)
        x = self.residual_block3(x)

        # (B,128,20)->(B,128*20)->(B,1)
        x = x.view(x.size(0), -1)
        x = self.fc1(x)
        x = self.fc2(x)

        # (B,1)->(B)
        x = x.squeeze()
        y = torch.sigmoid(x)

        return y

    def make_layer(self, in_channels, num_blocks):
        layers = []
        for i in range(0, num_blocks):
            layers.append(ResidualBlock(in_channels))
        return torch.nn.Sequential(*layers)


if __name__ == "__main__":
    model = yannet()
    params_num = sum(p.numel() for p in model.parameters())
    print(params_num)