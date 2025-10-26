class Messages {
    static system_message = Object.freeze({
        role: 'system',
        content: 'You (the "bot") are a chatbot designed to answer question about Mathieu Duchesneau. Answer the user to the best of your knowledge. If you do not know the answer, just say so. Do not invent information! Mathieu was born in Montréal in 1993. He has a PhD in machine learning which he did at the University of Montréal in the Mila laboratory. Specifically in learning equihash functions, a novel technique that extend the functionality of traditional hash functions.'
    })

    constructor() {
        this.container = document.getElementById('chat-messages');
        
        // TODO: Hide this in the chat template
        this.messages = [Messages.system_message];
        
        // TODO: Test if locale exists
        for (const message_div of this.container.childNodes) {
            if (message_div.tagName === "DIV") {
                let role = "assistant";
                if (message_div.classList.contains("user")) {
                    role = "user";
                }
                this.messages.push({role: role, content: message_div.textContent});
            }
        }
    }

    getMessages() {
        return this.messages;
    }

    focus_last() {
        this.container.scrollTop = this.container.scrollHeight;
    }

    displayMessage(role, content) {
        const message = document.createElement('div');
        message.textContent = content;
        message.classList.add('chat-message', role);
        this.container.appendChild(message);
        this.focus_last();
        return message;
    }

    push(role, content) {
        this.displayMessage(role, content);
        this.messages.push({role: role, content: content});
    }

    async push_stream(role, stream) {
        let content = "";
        const message = this.displayMessage(role, "");
        for await (const delta of stream) {
            content += delta
            message.textContent += delta;
            this.focus_last();
        }
      
        this.messages.push({role: role, content: content})
    }
}

class ChatbotAPI {
    constructor() {
        this.chat_prompt = document.getElementById('chat-prompt');
        this.chat_button = document.getElementById('chat-button');
        this.messages = new Messages();

        this.base_url = document.getElementById("chatbot-url").content
        this.models_url = new URL("v1/models", this.base_url).href;
        this.completions_url = new URL("v1/chat/completions", this.base_url).href;
        this.name = null;
        this.ready = false;

        if (name !== null) {
            this.ready = true;
        }
    }

    async fetchName() {
        try {
            const response = await fetch(this.models_url);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data = await response.json();
            const path = data.models[0].name;
            this.name = path.split("/").pop().replace(/\.[^.]+$/, "");
            this.ready = true;
        } catch (err) {
            console.error("Failed to fetch model info:", err); 
        }
    }

    async sendMessage() {
        if (this.chat_prompt.value === "") {
            return
        }
        this.chat_prompt.disabled = true;
        this.messages.push("user", this.chat_prompt.value);
        this.chat_prompt.value = "";

        await this.messages.push_stream("assistant", this.getResponseStream())
        this.chat_prompt.disabled = false;
        this.chat_prompt.focus();
    }

    async *getResponseStream() {
        if (!this.ready) {
            console.error("Chatbot is not available.");
            return;
        }

        const body = JSON.stringify({
            model: this.name,
            messages: this.messages.getMessages(),
            stream: true,
        })

        let response = await fetch(this.completions_url, {
            method: "POST",
            body: body,
        })

        if (!response.ok || !response.body) {
            console.error("Failed to start stream:", response.status, response.statusText);
            return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
          
            let lines = decoder.decode(value, { stream: true }).split('\n');
            for (let line of lines) {
                line = line.trim();
                if (line === "") continue;

                if (!line.startsWith("data: ")) {
                    console.log('SSE line does not start with "data: "');
                    console.log(line);
                    continue;
                }

                line = line.slice(6);

                if (line === "[DONE]") return;

                try {
                    const json = JSON.parse(line);
                    const delta = json.choices?.[0]?.delta?.content;
                    if (delta) yield delta;
                } catch (err) {
                    console.log("Error parsing delta:", err, line);
                }
            }
        }
    }
}

class ChatbotFrame {
    constructor() {
        this.opened_div = document.getElementById('opened-chatbot');
        this.closed_div = document.getElementById('closed-chatbot');
        this.minimize_button = document.getElementById('minimize-chatbot');
        this.info = document.getElementById("chatbot-info");
        this.footer = document.querySelector('footer');    
    }
    
    updatePosition() {
        const footerRect = this.footer.getBoundingClientRect();
        const windowHeight = window.innerHeight;

        let bottom = '12px';
        if (footerRect.top < windowHeight) {
            // Footer overlaps viewport → lift chatbot above it
            bottom = (windowHeight - footerRect.top + 12) + 'px';
            this.opened_div.style.height = `clamp(0px, calc(100vh - 24px - 1rem - 12px - ${(windowHeight - footerRect.top)}px), 500px)`;
        } else {
            // Footer not visible → keep at default
            this.opened_div.style.height = 'clamp(0px, calc(100vh - 24px - 1rem - 12px), 500px)';
        }
        this.opened_div.style.bottom = bottom;
        this.closed_div.style.bottom = bottom;
    }
    
    close() {
        this.opened_div.style.display = 'none';
        this.closed_div.style.display = 'flex';
    }

    open() {
        this.closed_div.style.display = 'none';
        this.opened_div.style.display = 'flex';
    }

    setInfo(name) {
        if (name === null) {
            this.info.textContent = "Service not available";
            return;
        }
        this.info.textContent = name
    }

}

class Chatbot {
    constructor(api) {
       this.api = new ChatbotAPI();
       this.frame = new ChatbotFrame();
    }

    async fetchInfo() {
        await this.api.fetchName();
        this.frame.setInfo(this.api.name);
    }
}

const chatbot = new Chatbot();
window.addEventListener('load', chatbot.frame.updatePosition.bind(chatbot.frame));
window.addEventListener('scroll', chatbot.frame.updatePosition.bind(chatbot.frame));
window.addEventListener('resize', chatbot.frame.updatePosition.bind(chatbot.frame));

chatbot.frame.minimize_button.addEventListener('click', chatbot.frame.close.bind(chatbot.frame));
chatbot.frame.closed_div.addEventListener('click', chatbot.frame.open.bind(chatbot.frame));

document.addEventListener("DOMContentLoaded", chatbot.fetchInfo.bind(chatbot));

chatbot.api.chat_button.addEventListener('click', chatbot.api.sendMessage.bind(chatbot.api));
chatbot.api.chat_prompt.addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
        event.preventDefault();
        chatbot.api.sendMessage();
    }
});
