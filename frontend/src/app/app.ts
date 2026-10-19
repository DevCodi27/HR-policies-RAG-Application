import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChatComponent } from './components/chat/chat.component';
import { DocumentManagementComponent } from './components/document-management/document-management.component';
import { TraceDashboardComponent } from './components/trace-dashboard/trace-dashboard.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, ChatComponent, DocumentManagementComponent, TraceDashboardComponent],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  readonly activeTab = signal<'chat' | 'documents' | 'traces'>('chat');

  setTab(tab: 'chat' | 'documents' | 'traces'): void {
    this.activeTab.set(tab);
  }
}
