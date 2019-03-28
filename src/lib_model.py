import torch
from torch.nn import functional as fun


class MyModel(torch.nn.Module):
    def __init__(self, res, anchors):
        super().__init__()

        self.res = res
        self.anchors = anchors
        self.n_anchor = len(anchors)
        self.scale = 16
        self.n_grid = int(self.res / self.scale)
        self.grid_res = self.scale

        self.anchor_tensor_w = torch.stack([torch.full((self.n_grid, self.n_grid), a.w) for a in self.anchors], dim=0)
        self.anchor_tensor_h = torch.stack([torch.full((self.n_grid, self.n_grid), a.h) for a in self.anchors], dim=0)

        self.grid_offset_x = torch.arange(float(self.n_grid)).repeat(self.n_grid, 1).mul(self.grid_res)
        self.grid_offset_y = self.grid_offset_x.t()

        self.feature_extractor = torch.nn.Sequential(
            torch.nn.Conv2d(1, 4, 3, padding=1),
            torch.nn.BatchNorm2d(4),
            torch.nn.ReLU(),
            torch.nn.MaxPool2d(2),
            #
            torch.nn.Conv2d(4, 8, 3, padding=1),
            torch.nn.BatchNorm2d(8),
            torch.nn.ReLU(),
            torch.nn.MaxPool2d(2),
            #
            torch.nn.Conv2d(8, 16, 3, padding=1),
            torch.nn.BatchNorm2d(16),
            torch.nn.ReLU(),
            torch.nn.MaxPool2d(2),
            #
            torch.nn.Conv2d(16, 32, 3, padding=1),
            torch.nn.BatchNorm2d(32),
            torch.nn.ReLU(),
            torch.nn.MaxPool2d(2),
            #
            torch.nn.Conv2d(32, 64, 3, padding=1),
            torch.nn.BatchNorm2d(64),
            torch.nn.ReLU(),
        )

        self.conv_c = torch.nn.Conv2d(32, self.n_anchor, 3, padding=1)
        self.conv_x = torch.nn.Conv2d(32, self.n_anchor, 3, padding=1)
        self.conv_y = torch.nn.Conv2d(32, self.n_anchor, 3, padding=1)
        self.conv_w = torch.nn.Conv2d(32, self.n_anchor, 3, padding=1)
        self.conv_h = torch.nn.Conv2d(32, self.n_anchor, 3, padding=1)

    def forward(self, inpt):
        features = self.feature_extractor(inpt)

        shape_1 = (-1, self.n_anchor, self.n_grid * self.n_grid)
        shape_2 = (-1, self.n_anchor, self.n_grid, self.n_grid)
        c = fun.softmax(self.conv_c(features).reshape(shape_1), dim=2).reshape(shape_2)

        x = fun.sigmoid(self.conv_x(features)).mul(self.grid_res).add(self.grid_offset_x)

        y = fun.sigmoid(self.conv_y(features)).mul(self.grid_res).add(self.grid_offset_y)

        w = fun.tanh(self.conv_w(features)).exp().mul(self.anchor_tensor_w)

        h = fun.tanh(self.conv_h(features)).exp().mul(self.anchor_tensor_h)

        return c, x, y, w, h


if __name__ == "__main__":
    pass