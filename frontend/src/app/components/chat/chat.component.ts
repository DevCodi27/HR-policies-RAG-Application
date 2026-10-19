import { Component, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PolicyChatService } from '../../core/services/policy-chat.service';
import { ChatMessage } from '../../core/models/policy-chat.model';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.css'
})
export class ChatComponent {
  private readonly chatService = inject(PolicyChatService);

  readonly userMessage = signal<string>('');
  readonly isLoading = signal<boolean>(false);
  readonly selectedEmployeeId = signal<string>('EMP-101');
  readonly selectedAgentMode = signal<'single' | 'multi'>('single');

  readonly employees = [
    { id: 'EMP-101', label: 'EMP-101 (Aarav Sharma - Grade 3, India)' },
    { id: 'EMP-102', label: 'EMP-102 (Eleanor Vance - Grade 6, UK)' },
    { id: 'EMP-103', label: 'EMP-103 (Priya Nair - Grade 1, India)' },
    { id: 'EMP-104', label: 'EMP-104 (Arthur Pendelton - Grade 5, UK)' },
  ];

  readonly messages = signal<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      text: 'Hello! I am your HR Policy Assistant powered by Qwen on Groq. Ask me about your entitlements, leave balances, or company policies.',
      timestamp: new Date(),
    },
  ]);

  onSendMessage(): void {
    const text = this.userMessage().trim();
    if (!text || this.isLoading()) return;

    const empId = this.selectedEmployeeId();
    const mode = this.selectedAgentMode();

    this.messages.update((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        sender: 'user',
        text: text,
        timestamp: new Date(),
      },
    ]);

    this.userMessage.set('');
    this.isLoading.set(true);

    this.chatService.sendMessage({ message: text, employee_id: empId, agent_mode: mode }).subscribe({
      next: (res) => {
        this.messages.update((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            sender: 'assistant',
            text: res.reply,
            timestamp: new Date(),
            metadata: {
              model: res.model,
              latency_sec: res.latency_sec,
              prompt_tokens: res.prompt_tokens,
              completion_tokens: res.completion_tokens,
              cost_usd: res.cost_usd,
              tool_calls_executed: res.tool_calls_executed,
              agent_mode: res.agent_mode || mode,
            },
          },
        ]);
        this.isLoading.set(false);
      },
      error: (err) => {
        this.messages.update((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            sender: 'assistant',
            text: `⚠️ Connection Error: Unable to reach FastAPI backend (${err.statusText || 'Offline'}). Make sure uvicorn is running on port 8000!`,
            timestamp: new Date(),
          },
        ]);
        this.isLoading.set(false);
      },
    });
  }

  setQuickPrompt(promptText: string): void {
    this.userMessage.set(promptText);
  }
}
