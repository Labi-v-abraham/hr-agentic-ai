-- ==================================================
-- HR Agentic AI - Production Supabase Schema
-- ==================================================

-- ==================================================
-- TYPES & ENUMS
-- ==================================================

DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
        CREATE TYPE user_role AS ENUM ('HR_ADMIN', 'HR_MANAGER');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_status') THEN
        CREATE TYPE user_status AS ENUM ('ACTIVE', 'INACTIVE');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'document_status') THEN
        CREATE TYPE document_status AS ENUM ('UPLOADED', 'PROCESSING', 'PROCESSED', 'FAILED');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'agent_type') THEN
        CREATE TYPE agent_type AS ENUM ('GENERAL', 'HR_POLICY', 'RESUME', 'EMAIL');
    END IF;
END $$;

-- ==================================================
-- TABLES
-- ==================================================

-- PROFILES
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_user_id UUID UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT CHECK (name <> ''),
    email TEXT UNIQUE NOT NULL CHECK (email <> ''),
    role user_role DEFAULT 'HR_MANAGER'::user_role,
    department TEXT,
    status user_status DEFAULT 'ACTIVE'::user_status,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ,
    last_activity TIMESTAMPTZ
);

COMMENT ON TABLE public.profiles IS 'Stores user profiles seamlessly synced with Supabase auth.users';
COMMENT ON COLUMN public.profiles.auth_user_id IS 'Foreign key referencing auth.users';
COMMENT ON COLUMN public.profiles.role IS 'User permission role restricted to HR_ADMIN or HR_MANAGER';

-- DOCUMENTS
CREATE TABLE IF NOT EXISTS public.documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL CHECK (name <> ''),
    file_path TEXT NOT NULL CHECK (file_path <> ''),
    mime_type TEXT,
    file_size BIGINT,
    storage_bucket TEXT,
    storage_path TEXT,
    uploaded_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    status document_status DEFAULT 'UPLOADED'::document_status,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE public.documents IS 'Stores metadata for HR documents and files uploaded to the AI system';
COMMENT ON COLUMN public.documents.is_deleted IS 'Soft delete flag ensuring documents remain for audit trails if needed';

-- CHAT HISTORY
CREATE TABLE IF NOT EXISTS public.chat_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    session_id UUID DEFAULT gen_random_uuid() NOT NULL,
    question TEXT NOT NULL CHECK (question <> ''),
    response TEXT NOT NULL CHECK (response <> ''),
    agent_used agent_type NOT NULL,
    llm_used TEXT NOT NULL CHECK (llm_used <> ''),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE public.chat_history IS 'Logs AI interactions per user and session';
COMMENT ON COLUMN public.chat_history.session_id IS 'Groups messages into a single conversational session';

-- AUDIT LOGS
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    action TEXT NOT NULL CHECK (action <> ''),
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE public.audit_logs IS 'Immutable ledger tracking significant administrative actions within the application';

-- ==================================================
-- INDEXES
-- ==================================================

-- Profiles
CREATE INDEX IF NOT EXISTS idx_profiles_auth_user_id ON public.profiles(auth_user_id);
CREATE INDEX IF NOT EXISTS idx_profiles_email ON public.profiles(email);
CREATE INDEX IF NOT EXISTS idx_profiles_role ON public.profiles(role);

-- Documents
CREATE INDEX IF NOT EXISTS idx_documents_uploaded_by ON public.documents(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_documents_status ON public.documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_is_deleted ON public.documents(is_deleted);

-- Chat History
CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON public.chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_session_id ON public.chat_history(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_created_at ON public.chat_history(created_at);

-- Audit Logs
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON public.audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON public.audit_logs(created_at);

-- ==================================================
-- SECURITY DEFINER HELPER FUNCTIONS
-- ==================================================

-- Retrieve the current user's profile UUID efficiently
CREATE OR REPLACE FUNCTION public.current_profile_id()
RETURNS UUID AS $$
DECLARE
    v_profile_id UUID;
BEGIN
    SELECT id INTO v_profile_id
    FROM public.profiles
    WHERE auth_user_id = auth.uid();
    RETURN v_profile_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

GRANT EXECUTE ON FUNCTION public.current_profile_id() TO authenticated;
COMMENT ON FUNCTION public.current_profile_id() IS 'Securely returns the internal profile UUID of the authenticated user to avoid recursive RLS';


-- Check if the current user holds the HR_ADMIN role
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.profiles 
        WHERE auth_user_id = auth.uid() AND role = 'HR_ADMIN'::user_role
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

GRANT EXECUTE ON FUNCTION public.is_admin() TO authenticated;
COMMENT ON FUNCTION public.is_admin() IS 'Securely validates HR_ADMIN permissions without recursive RLS';


-- Check if the current user holds the HR_MANAGER role
CREATE OR REPLACE FUNCTION public.is_manager()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.profiles 
        WHERE auth_user_id = auth.uid() AND role = 'HR_MANAGER'::user_role
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

GRANT EXECUTE ON FUNCTION public.is_manager() TO authenticated;
COMMENT ON FUNCTION public.is_manager() IS 'Securely validates HR_MANAGER permissions without recursive RLS';

-- ==================================================
-- TRIGGERS
-- ==================================================

-- Function to automatically update 'updated_at' columns
CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update_updated_at to profiles
DROP TRIGGER IF EXISTS trg_profiles_updated_at ON public.profiles;
CREATE TRIGGER trg_profiles_updated_at
BEFORE UPDATE ON public.profiles
FOR EACH ROW
EXECUTE FUNCTION public.update_updated_at();

-- Apply update_updated_at to documents
DROP TRIGGER IF EXISTS trg_documents_updated_at ON public.documents;
CREATE TRIGGER trg_documents_updated_at
BEFORE UPDATE ON public.documents
FOR EACH ROW
EXECUTE FUNCTION public.update_updated_at();


-- Handle new user registration automatically when auth.users is populated
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
    assigned_role user_role;
    display_name TEXT;
BEGIN
    -- Role Assignment
    IF NEW.email = 'admin@hragent.ai' THEN
        assigned_role := 'HR_ADMIN'::user_role;
    ELSE
        assigned_role := 'HR_MANAGER'::user_role;
    END IF;

    -- Secure Name Parsing
    display_name := COALESCE(
        NEW.raw_user_meta_data->>'name',
        split_part(NEW.email, '@', 1)
    );

    -- Insert Profile
    INSERT INTO public.profiles (auth_user_id, email, role, name)
    VALUES (NEW.id, NEW.email, assigned_role, display_name);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Trigger for auth.users
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
AFTER INSERT ON auth.users
FOR EACH ROW
EXECUTE FUNCTION public.handle_new_user();

-- ==================================================
-- ROW LEVEL SECURITY (RLS)
-- ==================================================

-- PROFILES
-- RLS disabled on profiles explicitly.
-- We rely on the Python Backend + Service Role Key to manage profile records securely.
-- This prevents the "infinite recursion" error fundamentally.
ALTER TABLE public.profiles DISABLE ROW LEVEL SECURITY;

-- DOCUMENTS
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Authenticated HR users can read non-deleted documents" ON public.documents;
DROP POLICY IF EXISTS "HR_ADMIN and HR_MANAGER can upload documents" ON public.documents;
DROP POLICY IF EXISTS "HR_ADMIN and HR_MANAGER can update documents" ON public.documents;
DROP POLICY IF EXISTS "Only HR_ADMIN can delete documents" ON public.documents;

CREATE POLICY "Authenticated HR users can read non-deleted documents"
    ON public.documents FOR SELECT
    TO authenticated
    USING ((public.is_admin() OR public.is_manager()) AND is_deleted = FALSE);

CREATE POLICY "HR_ADMIN and HR_MANAGER can upload documents"
    ON public.documents FOR INSERT
    TO authenticated
    WITH CHECK (public.is_admin() OR public.is_manager());

CREATE POLICY "HR_ADMIN and HR_MANAGER can update documents"
    ON public.documents FOR UPDATE
    TO authenticated
    USING (public.is_admin() OR public.is_manager());

CREATE POLICY "Only HR_ADMIN can delete documents"
    ON public.documents FOR DELETE
    TO authenticated
    USING (public.is_admin());

-- CHAT HISTORY
ALTER TABLE public.chat_history ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can manage their own chat history" ON public.chat_history;

CREATE POLICY "Users can manage their own chat history"
    ON public.chat_history FOR ALL
    TO authenticated
    USING (user_id = public.current_profile_id())
    WITH CHECK (user_id = public.current_profile_id());

-- AUDIT LOGS
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Only HR_ADMIN can read audit logs" ON public.audit_logs;

CREATE POLICY "Only HR_ADMIN can read audit logs"
    ON public.audit_logs FOR SELECT
    TO authenticated
    USING (public.is_admin());
