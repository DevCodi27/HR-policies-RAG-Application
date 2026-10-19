import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PolicyChatService } from '../../core/services/policy-chat.service';
import { PolicyDocumentItem } from '../../core/models/policy-chat.model';

@Component({
  selector: 'app-document-management',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './document-management.component.html',
  styleUrl: './document-management.component.css'
})
export class DocumentManagementComponent implements OnInit {
  private readonly chatService = inject(PolicyChatService);

  readonly documents = signal<PolicyDocumentItem[]>([]);
  readonly isLoading = signal<boolean>(false);
  readonly isUploading = signal<boolean>(false);

  // Form Signals
  readonly docTitle = signal<string>('');
  readonly docEntity = signal<'India' | 'UK' | 'Global'>('India');
  readonly docVersion = signal<string>('v2025.1');
  readonly docEffectiveDate = signal<string>('2025-01-01');
  readonly selectedFile = signal<File | null>(null);

  readonly statusMessage = signal<{ type: 'success' | 'error'; text: string } | null>(null);

  ngOnInit(): void {
    this.loadDocuments();
  }

  loadDocuments(): void {
    this.isLoading.set(true);
    this.chatService.getDocuments().subscribe({
      next: (res) => {
        this.documents.set(res.documents);
        this.isLoading.set(false);
      },
      error: (err) => {
        this.statusMessage.set({
          type: 'error',
          text: `Failed to load documents from MySQL: ${err.message || 'Unknown error'}`
        });
        this.isLoading.set(false);
      }
    });
  }

  onFileChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.selectedFile.set(input.files[0]);
    }
  }

  onUpload(): void {
    const file = this.selectedFile();
    const title = this.docTitle().trim();
    if (!file || !title || this.isUploading()) {
      this.statusMessage.set({
        type: 'error',
        text: 'Please provide a document title and select a .pdf, .docx, or .md file.'
      });
      return;
    }

    this.isUploading.set(true);
    this.statusMessage.set(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    formData.append('entity', this.docEntity());
    formData.append('version', this.docVersion().trim());
    formData.append('effective_date', this.docEffectiveDate().trim());

    this.chatService.uploadDocument(formData).subscribe({
      next: (newDoc) => {
        this.statusMessage.set({
          type: 'success',
          text: `Successfully uploaded "${newDoc.title}"! Parsed and saved ${newDoc.total_chunks} clause chunks to MySQL.`
        });
        this.isUploading.set(false);
        this.docTitle.set('');
        this.selectedFile.set(null);
        this.loadDocuments();
      },
      error: (err) => {
        this.statusMessage.set({
          type: 'error',
          text: `Upload failed: ${err.error?.detail || err.message || 'Server error'}`
        });
        this.isUploading.set(false);
      }
    });
  }

  onDelete(id: number): void {
    if (!confirm('Are you sure you want to delete this document and its clause chunks?')) {
      return;
    }

    this.chatService.deleteDocument(id).subscribe({
      next: () => {
        this.statusMessage.set({
          type: 'success',
          text: 'Document and cascading chunks deleted from MySQL.'
        });
        this.loadDocuments();
      },
      error: (err) => {
        this.statusMessage.set({
          type: 'error',
          text: `Failed to delete document: ${err.error?.detail || err.message}`
        });
      }
    });
  }
}
