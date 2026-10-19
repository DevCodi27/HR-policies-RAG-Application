import { Component, signal, computed, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PolicyChatService } from '../../core/services/policy-chat.service';
import { TraceRecord, TraceMetrics } from '../../core/models/policy-chat.model';

@Component({
  selector: 'app-trace-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './trace-dashboard.component.html',
  styleUrl: './trace-dashboard.component.css'
})
export class TraceDashboardComponent implements OnInit {
  private readonly chatService = inject(PolicyChatService);

  readonly traces = signal<TraceRecord[]>([]);
  readonly metrics = signal<TraceMetrics | null>(null);
  readonly selectedTrace = signal<TraceRecord | null>(null);
  readonly filterMode = signal<'all' | 'single' | 'multi'>('all');
  readonly searchTerm = signal<string>('');
  readonly isLoading = signal<boolean>(false);
  readonly errorMessage = signal<string | null>(null);

  readonly filteredTraces = computed(() => {
    const list = this.traces();
    const mode = this.filterMode();
    const search = this.searchTerm().toLowerCase().trim();

    return list.filter((t) => {
      const matchesMode = mode === 'all' || t.agent_mode === mode;
      const matchesSearch =
        !search ||
        t.employee_id.toLowerCase().includes(search) ||
        t.query.toLowerCase().includes(search) ||
        t.trace_id.toLowerCase().includes(search) ||
        t.reply.toLowerCase().includes(search);

      return matchesMode && matchesSearch;
    });
  });

  ngOnInit(): void {
    this.loadTraces();
  }

  loadTraces(): void {
    this.isLoading.set(true);
    this.errorMessage.set(null);

    this.chatService.getTraces().subscribe({
      next: (res) => {
        this.metrics.set(res.metrics);
        this.traces.set(res.traces);
        if (res.traces.length > 0 && !this.selectedTrace()) {
          this.selectedTrace.set(res.traces[0]);
        }
        this.isLoading.set(false);
      },
      error: (err) => {
        this.errorMessage.set(`Failed to load traces from backend: ${err.message || 'Offline'}`);
        this.isLoading.set(false);
      }
    });
  }

  selectTrace(trace: TraceRecord): void {
    this.selectedTrace.set(trace);
  }

  openLangfuse(): void {
    window.open('https://cloud.langfuse.com', '_blank');
  }
}
