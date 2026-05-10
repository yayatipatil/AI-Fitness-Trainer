import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
import random
import math

MODEL_PATH = os.path.join(os.path.dirname(__file__), "seq2seq_model.pt")
VOCAB_PATH = os.path.join(os.path.dirname(__file__), "seq2seq_vocab.json")

# Special tokens
PAD_TOKEN = 0
SOS_TOKEN = 1
EOS_TOKEN = 2

DB_PATH = os.path.join(os.path.dirname(__file__), "exercises_db.json")

def get_all_exercises():
    with open(DB_PATH, 'r') as f:
        return json.load(f)

class WorkoutSeq2Seq(nn.Module):
    def __init__(self, input_dim, hidden_dim, vocab_size, num_layers=1):
        super(WorkoutSeq2Seq, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.vocab_size = vocab_size
        
        # Map input features to hidden state and cell state for LSTM
        self.fc_hidden = nn.Linear(input_dim, hidden_dim * num_layers)
        self.fc_cell = nn.Linear(input_dim, hidden_dim * num_layers)
        
        # Decoder
        self.embedding = nn.Embedding(vocab_size, hidden_dim)
        self.lstm = nn.LSTM(hidden_dim, hidden_dim, num_layers, batch_first=True)
        self.fc_out = nn.Linear(hidden_dim, vocab_size)
        
    def forward(self, features, trg, teacher_forcing_ratio=0.5):
        # features: (batch_size, input_dim)
        # trg: (batch_size, trg_len)
        batch_size = features.shape[0]
        trg_len = trg.shape[1]
        
        outputs = torch.zeros(batch_size, trg_len, self.vocab_size).to(features.device)
        
        # Initialize hidden and cell states from features
        h0 = self.fc_hidden(features).view(batch_size, self.num_layers, self.hidden_dim).transpose(0, 1).contiguous()
        c0 = self.fc_cell(features).view(batch_size, self.num_layers, self.hidden_dim).transpose(0, 1).contiguous()
        
        hidden = (h0, c0)
        
        input = trg[:, 0] # SOS token
        
        for t in range(1, trg_len):
            embedded = self.embedding(input).unsqueeze(1) # (batch_size, 1, hidden_dim)
            output, hidden = self.lstm(embedded, hidden)
            prediction = self.fc_out(output.squeeze(1)) # (batch_size, vocab_size)
            
            outputs[:, t, :] = prediction
            
            teacher_force = random.random() < teacher_forcing_ratio
            top1 = prediction.argmax(1)
            
            input = trg[:, t] if teacher_force else top1
            
        return outputs

    def generate(self, features, max_len=10):
        self.eval()
        with torch.no_grad():
            batch_size = features.shape[0]
            
            h0 = self.fc_hidden(features).view(batch_size, self.num_layers, self.hidden_dim).transpose(0, 1).contiguous()
            c0 = self.fc_cell(features).view(batch_size, self.num_layers, self.hidden_dim).transpose(0, 1).contiguous()
            
            hidden = (h0, c0)
            
            input = torch.tensor([SOS_TOKEN] * batch_size).to(features.device)
            
            generated_seqs = [[] for _ in range(batch_size)]
            
            for _ in range(max_len):
                embedded = self.embedding(input).unsqueeze(1)
                output, hidden = self.lstm(embedded, hidden)
                prediction = self.fc_out(output.squeeze(1))
                top1 = prediction.argmax(1)
                
                input = top1
                
                for i in range(batch_size):
                    token = top1[i].item()
                    generated_seqs[i].append(token)
                    
            return generated_seqs

def get_vocab():
    if os.path.exists(VOCAB_PATH):
        with open(VOCAB_PATH, 'r') as f:
            return json.load(f)
            
    # Build vocabulary
    vocab = {"<PAD>": PAD_TOKEN, "<SOS>": SOS_TOKEN, "<EOS>": EOS_TOKEN}
    idx = 3
    db_ex = get_all_exercises()
    for ex in db_ex:
        name = ex["name"]
        if name not in vocab:
            vocab[name] = idx
            idx += 1
            
    with open(VOCAB_PATH, 'w') as f:
        json.dump(vocab, f)
    return vocab

def generate_synthetic_data(num_samples=1000):
    vocab = get_vocab()
    db_ex = get_all_exercises()
    
    # Categorize exercises
    weight_loss_pool = [e["name"] for e in db_ex if e["type"] == "cardio" or "Full Body" in e["muscle_group"]]
    muscle_gain_pool = [e["name"] for e in db_ex if e["type"] == "strength"]
    maintenance_pool = [e["name"] for e in db_ex]
    
    X = []
    Y = []
    
    goals = ['weight loss', 'muscle gain', 'maintenance']
    levels = ['beginner', 'intermediate', 'advanced']
    
    for _ in range(num_samples):
        goal = random.choice(goals)
        level = random.choice(levels)
        intensity = random.uniform(0.5, 2.0)
        duration = random.choice([5, 15, 30, 45, 60])
        
        # Feature encoding
        g_idx = goals.index(goal)
        l_idx = levels.index(level)
        
        # One-hot goal (3), One-hot level (3), intensity (1), duration (1) => 8 dims
        feat = [0]*3 + [0]*3 + [intensity, duration/60.0]
        feat[g_idx] = 1.0
        feat[3 + l_idx] = 1.0
        X.append(feat)
        
        # Sequence generation rules for synthetic training
        seq = [vocab["<SOS>"]]
        num_exercises = max(1, min(8, int(duration / 5)))
        
        if goal == 'weight loss':
            pool = weight_loss_pool
        elif goal == 'muscle gain':
            pool = muscle_gain_pool
        else:
            pool = maintenance_pool
            
        chosen = random.sample(pool, min(num_exercises, len(pool)))
        for ex in chosen:
            if ex in vocab:
                seq.append(vocab[ex])
        seq.append(vocab["<EOS>"])
        
        # Pad to max len (10)
        while len(seq) < 10:
            seq.append(vocab["<PAD>"])
            
        Y.append(seq[:10])
        
    return torch.tensor(X, dtype=torch.float32), torch.tensor(Y, dtype=torch.long)

def train_model():
    print("Training Seq2Seq workout recommendation model...")
    vocab = get_vocab()
    vocab_size = len(vocab)
    input_dim = 8
    hidden_dim = 64
    
    model = WorkoutSeq2Seq(input_dim, hidden_dim, vocab_size)
    optimizer = optim.Adam(model.parameters(), lr=0.01)
    criterion = nn.CrossEntropyLoss(ignore_index=PAD_TOKEN)
    
    X_train, Y_train = generate_synthetic_data(2000)
    
    model.train()
    epochs = 50
    batch_size = 32
    
    for epoch in range(epochs):
        epoch_loss = 0
        for i in range(0, len(X_train), batch_size):
            batch_X = X_train[i:i+batch_size]
            batch_Y = Y_train[i:i+batch_size]
            
            optimizer.zero_grad()
            output = model(batch_X, batch_Y)
            
            # output: (batch, seq_len, vocab_size)
            # batch_Y: (batch, seq_len)
            output_dim = output.shape[-1]
            
            output = output[:, 1:].reshape(-1, output_dim)
            trg = batch_Y[:, 1:].reshape(-1)
            
            loss = criterion(output, trg)
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            
        if (epoch+1) % 10 == 0:
            print(f"Epoch {epoch+1}/{epochs} | Loss: {epoch_loss / (len(X_train)/batch_size):.4f}")
            
    torch.save(model.state_dict(), MODEL_PATH)
    print("Model saved to", MODEL_PATH)
    return model

def load_model():
    vocab = get_vocab()
    vocab_size = len(vocab)
    input_dim = 8
    hidden_dim = 64
    
    model = WorkoutSeq2Seq(input_dim, hidden_dim, vocab_size)
    if not os.path.exists(MODEL_PATH):
        train_model()
    model.load_state_dict(torch.load(MODEL_PATH, weights_only=True))
    model.eval()
    return model

def predict_workout_sequence(goal: str, level: str, intensity: float, duration: int) -> list:
    model = load_model()
    vocab = get_vocab()
    inv_vocab = {v: k for k, v in vocab.items()}
    
    goals = ['weight loss', 'muscle gain', 'maintenance']
    levels = ['beginner', 'intermediate', 'advanced']
    
    # Safely handle unknown inputs
    g_str = goal.lower()
    l_str = level.lower()
    if g_str not in goals: g_str = 'maintenance'
    if l_str not in levels: l_str = 'beginner'
    
    g_idx = goals.index(g_str)
    l_idx = levels.index(l_str)
    
    feat = [0]*3 + [0]*3 + [intensity, duration/60.0]
    feat[g_idx] = 1.0
    feat[3 + l_idx] = 1.0
    
    X = torch.tensor([feat], dtype=torch.float32)
    
    seq = model.generate(X, max_len=10)[0]
    
    exercises = []
    for token_id in seq:
        if token_id == EOS_TOKEN:
            break
        if token_id != PAD_TOKEN and token_id != SOS_TOKEN:
            exercises.append(inv_vocab.get(token_id, "Plank"))
            
    return exercises

if __name__ == "__main__":
    train_model()
