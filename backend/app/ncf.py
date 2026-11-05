import torch
import torch.nn as nn

class NCF(nn.Module):
    def __init__(self, num_users: int, num_items: int, embed_dim: int = 32):
        super(NCF, self).__init__()
        self.embed_user_gmf = nn.Embedding(num_users, embed_dim)
        self.embed_item_gmf = nn.Embedding(num_items, embed_dim)
        self.embed_user_mlp = nn.Embedding(num_users, embed_dim)
        self.embed_item_mlp = nn.Embedding(num_items, embed_dim)
        
        self.mlp_layers = nn.Sequential(
            nn.Linear(embed_dim * 2, 64),
            nn.ReLU(),
            nn.Dropout(0.2), # Thêm Dropout để chống Overfitting
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 16),
            nn.ReLU()
        )
        self.final_layer = nn.Linear(embed_dim + 16, 1)

    def forward(self, user_indices, item_indices):
        user_gmf = self.embed_user_gmf(user_indices)
        item_gmf = self.embed_item_gmf(item_indices)
        gmf_out = user_gmf * item_gmf
        
        user_mlp = self.embed_user_mlp(user_indices)
        item_mlp = self.embed_item_mlp(item_indices)
        mlp_in = torch.cat([user_mlp, item_mlp], dim=-1)
        mlp_out = self.mlp_layers(mlp_in)
        
        concat_out = torch.cat([gmf_out, mlp_out], dim=-1)
        output = self.final_layer(concat_out)
        
        return output.squeeze(-1) # Preserve batch dimension for a one-example batch.

    def predict(self, user_indices, item_indices):
        # Hàm riêng dùng khi Đánh giá, có Sigmoid để ép về 0-1
        return torch.sigmoid(self.forward(user_indices, item_indices))
