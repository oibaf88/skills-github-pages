alter function public.set_updated_at() set search_path = pg_catalog;
alter function public.psychapp_request_header(text) set search_path = pg_catalog;

revoke execute on function public.handle_new_user() from public;
revoke execute on function public.handle_new_user() from anon;
revoke execute on function public.handle_new_user() from authenticated;
revoke execute on function public.handle_new_user() from service_role;
grant execute on function public.handle_new_user() to supabase_auth_admin;
