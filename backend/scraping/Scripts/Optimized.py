import torch
import whisper
import torchaudio

# Load the Whisper model
model = whisper.load_model("medium")

# Example input for tracing
example_input = torch.randn(1, 80, 3000)  # Adjust the dimensions as needed
tokens = torch.randint(0, 1000, (1, 80))  # Example tokens input, adjust as needed

# Trace the model
scripted_model = torch.jit.trace(model, (example_input, tokens))

# Save the scripted model
scripted_model.save("whisper_medium_scripted.pt")

device = "cuda" if torch.cuda.is_available() else "cpu"
# Load the scripted model
loaded_model = torch.jit.load("whisper_medium_scripted.pt")

# Preprocess the audio input
audio_path = "C:/Users/damorena/_Modulos/Facu/ProyectoDeGrado/ProyectoDeGrado/DB/Opens/aali/output.wav"
waveform, sample_rate = torchaudio.load(audio_path, backend='soundfile')
waveform = whisper.pad_or_trim(waveform.flatten())
mel = whisper.log_mel_spectrogram(waveform).to(device)

# Generate tokens (this is a placeholder, replace with actual token generation logic)
tokens = torch.randint(0, 1000, (1, 80)).to(device)

# Run the model
with torch.no_grad():
    result = loaded_model(mel.unsqueeze(0), tokens)

# Postprocess the output
decoded = whisper.decode(model, result)
print(decoded['text'])