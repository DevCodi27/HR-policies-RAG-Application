import { Injectable, inject } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import { Observable } from "rxjs";
import { 
  ChatQueryRequest, 
  ChatQueryResponse, 
  PolicyDocumentItem, 
  DocumentListResponse,
  TraceDashboardResponse
} from "../models/policy-chat.model";

@Injectable({
  providedIn: 'root',
})
export class PolicyChatService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = 'http://localhost:8000/api/v1';

  sendMessage(request: ChatQueryRequest): Observable<ChatQueryResponse> {
    return this.http.post<ChatQueryResponse>(`${this.baseUrl}/chat`, request);
  }

  getDocuments(): Observable<DocumentListResponse> {
    return this.http.get<DocumentListResponse>(`${this.baseUrl}/documents`);
  }

  uploadDocument(formData: FormData): Observable<PolicyDocumentItem> {
    return this.http.post<PolicyDocumentItem>(`${this.baseUrl}/documents/upload`, formData);
  }

  deleteDocument(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/documents/${id}`);
  }

  getTraces(): Observable<TraceDashboardResponse> {
    return this.http.get<TraceDashboardResponse>(`${this.baseUrl}/traces`);
  }
}