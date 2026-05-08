// audio-coach.js

class AudioCoach {
    constructor() {
        this.synth = window.speechSynthesis;
        this.enabled = true;
        this.voice = null;
        this.lastSpoken = 0;
        
        // Wait for voices to be loaded
        if (speechSynthesis.onvoiceschanged !== undefined) {
            speechSynthesis.onvoiceschanged = () => this.initVoice();
        } else {
            this.initVoice();
        }
    }

    initVoice() {
        const voices = this.synth.getVoices();
        // Try to find a good English voice
        this.voice = voices.find(v => v.lang.includes('en') && (v.name.includes('Google') || v.name.includes('Samantha'))) || voices[0];
    }

    speak(text, priority = false) {
        if (!this.enabled || !this.synth) return;
        
        const now = Date.now();
        // Prevent spamming the same/similar feedback too often (cooldown 3s), unless priority
        if (!priority && (now - this.lastSpoken < 3000)) return;
        
        // Cancel currently playing speech if priority
        if (priority && this.synth.speaking) {
            this.synth.cancel();
        }

        const utterance = new SpeechSynthesisUtterance(text);
        if (this.voice) utterance.voice = this.voice;
        utterance.rate = 1.1; // Slightly faster for workout context
        utterance.pitch = 1.0;
        
        this.synth.speak(utterance);
        this.lastSpoken = now;
    }

    toggle(enabled) {
        this.enabled = enabled;
        if (!this.enabled && this.synth.speaking) {
            this.synth.cancel();
        }
    }
}

window.audioCoach = new AudioCoach();
