export interface User {
  id: string;
  email: string;
  username: string;
  role: 'admin' | 'owner' | 'viewer';
}

export interface DocumentPermission {
  id: string;
  document_id: string;
  grantee_id: string;
  grantee_username: string;
  grantee_email: string;
  can_read: boolean;
  can_edit: boolean;
  is_active: boolean;
}

export interface Document {
  id: string;
  title: string;
  original_filename: string;
  mime_type: string;
  file_size: number;
  file_hash_sha256: string;
  category: string;
  owner_id: string;
  owner_username?: string;
  created_at: string;
  permissions: DocumentPermission[];
}

export interface AuditLog {
  id: number;
  uuid_str: string;
  timestamp: string;
  user_id: string | null;
  document_id: string | null;
  action: string;
  metadata_json: string;
  previous_hash: string;
  current_hash: string;
}

export interface SystemMetrics {
  total_documents: number;
  total_users: number;
  active_permissions: number;
  total_audit_events: number;
  chain_status?: string;
  chain_integrity?: {
    status: string;
    total_records: number;
    message: string;
  };
}

export function formatBytes(bytes: number, decimals = 1): string {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}
