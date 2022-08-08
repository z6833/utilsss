#!/usr/bin/env python3

"""
@author: y00520910
@since:
"""

import argparse
import os

import numpy as np

import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

import optim as optim_
from dataset import WiFiDenoiseDataset
from net import yannet


device = 'cuda' if torch.cuda.is_available() else 'cpu'


class Trainer(object):

    def __init__(self,
                 model: torch.nn.Module,
                 max_lr,
                 weight_decay,
                 num_loops):
        self._model = model
        self._parameters = list(self._model.parameters())
        self._opt = torch.optim.AdamW(
            self._parameters,
            lr=max_lr,
            weight_decay=weight_decay
        )
        self._train_scheduler = optim_.CosineWarmupAnnealingLR(self._opt, num_loops)
        self.loss_func = torch.nn.MSELoss()

    def train(self, query, key, target):
        query = query.to(device).float()
        key = key.to(device).float()
        target = target.to(device).float()

        output = self._model(query, key)  # B
        output = output * 100

        loss = self.loss_func(output, target)

        loss.backward()
        self._opt.step()
        self._opt.zero_grad()
        self._train_scheduler.step()

        return loss.cpu(), self._train_scheduler.get_last_lr()[0]

    def predict(self, query, key):
        with torch.no_grad():
            query = query.to(device).float()
            key = key.to(device).float()

            output = self._model(query, key)
            output = output * 100
            return output.cpu()


def evaluate(trainer: Trainer, test_loader: DataLoader):
    res = []

    for doc in tqdm(test_loader, leave=False, dynamic_ncols=True, desc='Evaluate'):
        output = trainer.predict(doc['query'], doc['key'])
        target = doc['target']

        for k in range(target.size(0)):
            if abs(output[k] - target[k]) <= 5:
                res.append(1)
            elif 10 >= abs(output[k] - target[k]) > 5:
                res.append(0.6)
            else:
                res.append(0)

    accuracy = np.array(res).mean()

    return accuracy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset_dir', required=True)
    parser.add_argument('--gpu', default=[0, 1, 2, 3])
    parser.add_argument('--batch-size', type=int, default=1024)
    parser.add_argument('--max-lr', type=float, default=1e-3)
    parser.add_argument('--weight-decay', type=float, default=0.1)
    parser.add_argument('--num-epochs', type=int, default=50)
    parser.add_argument('--output_dir', type=str, default='./output_models')
    parser.add_argument('--tensorboard_dir', type=str, default='./tensorboard_')

    args = parser.parse_args()

    dataset_dir_list = args.dataset_dir.split(';')
    dataset_dir_dict = {}
    for data_dir_i in dataset_dir_list:
        content = data_dir_i.split(':')
        dataset_dir_dict[content[0]] = content[1]

    train_loader = DataLoader(
        WiFiDenoiseDataset(True,
                           dataset_dir_dict['databaseIp'],
                           dataset_dir_dict['databaseName'],
                           dataset_dir_dict['collectionName'],
                           dataset_dir_dict['username'],
                           dataset_dir_dict['password']),
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=32
    )
    test_loader = DataLoader(
        WiFiDenoiseDataset(False,
                           dataset_dir_dict['databaseIp'],
                           dataset_dir_dict['databaseName'],
                           dataset_dir_dict['collectionName'],
                           dataset_dir_dict['username'],
                           dataset_dir_dict['password']),
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=4
    )
    model = yannet()
    if device == 'cuda':
        model = torch.nn.DataParallel(model.to(device), device_ids=args.gpu)
    trainer = Trainer(
        model,
        max_lr=args.max_lr,
        weight_decay=args.weight_decay,
        num_loops=len(train_loader) * args.num_epochs
    )

    loss_g = 0.0
    accuracy_epochs = []
    loss_g_epochs = []
    loss_epochs = []
    for epoch in range(args.num_epochs):
        model.train()
        loop = tqdm(train_loader, leave=False, dynamic_ncols=True)
        this_epoch_loss = []
        for i, doc in enumerate(loop):
            loss, lr = trainer.train(doc['query'], doc['key'], doc['target'])
            loss = loss.detach().numpy()

            loss_g = 0.9 * loss_g + 0.1 * loss
            this_epoch_loss.append(loss)

            loop.set_description(f'Epoch: {epoch} L={loss_g:.06f}, LR={lr:.01e}', False)

        model.eval()
        accuracy = evaluate(trainer, test_loader)
        tqdm.write(
            f'Epoch: {epoch} L_this={np.mean(this_epoch_loss):.06f} L={loss_g:.06f} Accuracy={accuracy:.06f}'
        )
        state = {
            'state': model.state_dict(),
            'epoch': epoch,
        }
        latest_path = os.path.join(args.output_dir, 'latest.tar')
        if not os.path.exists(args.output_dir):
            os.mkdir(args.output_dir)
        torch.save(state, latest_path)

        accuracy_epochs.append(round(accuracy * 100, 2))
        loss_g_epochs.append(round(loss_g, 2))
        loss_epochs.append(round(np.array(this_epoch_loss).mean(), 2))

    # 画图
    print(f'\n"accuracy_epochs": {accuracy_epochs},')
    print(f'"loss_g_epochs": {loss_g_epochs},')
    print(f'"loss_epochs": {loss_epochs},')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
