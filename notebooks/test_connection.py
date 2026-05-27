from du_an_tot_nghiep.database import get_client

supabase = get_client()

try:
    result = supabase.table("users").select("*").limit(1).execute()
    print("Ket noi thanh cong!")
    print(result)
except Exception as e:
    if "PGRST205" in str(e):
        print("Ket noi Supabase thanh cong! (Chua co table nao)")
    else:
        print(f"Loi: {e}")
