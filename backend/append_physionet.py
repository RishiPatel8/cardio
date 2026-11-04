with open(r'd:\cardiogaurd\backend\app\api\v1\predictions\physionet.py', 'a') as f:
    f.write('''

@router.post("/compare")
async def compare_models(
    files: List[UploadFile] = File(...),
    age: float = Form(None),
    sex: int = Form(None),
    model_ids: str = Form(None),
    current_user: User = Depends(get_current_user)
):
    temp_dir = tempfile.mkdtemp()
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
            
        saved_files = {}
        for file in files:
            file_path = os.path.join(temp_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            ext = os.path.splitext(file.filename)[1].lower()
            saved_files[ext] = file.filename

        sig = []
        fs = 125.0
        
        if ".csv" in saved_files:
            csv_path = os.path.join(temp_dir, saved_files[".csv"])
            fs = 100.0
            df = pd.read_csv(csv_path, header=None)
            if df.shape[1] == 1:
                sig = df.iloc[:, 0].values.tolist()
            elif df.shape[1] >= 2:
                try:
                    float(df.iloc[0, 1])
                    sig = df.iloc[:, 1].values.tolist()
                except ValueError:
                    sig = df.iloc[1:, 1].values.astype(float).tolist()
            else:
                sig = df.iloc[:, 0].values.tolist()

        orchestrator = get_orchestrator()
        payload = {
            "waveform": sig,
            "age": age,
            "sex": sex,
            "fs": fs
        }
        
        if model_ids:
            ids_list = [m.strip() for m in model_ids.split(",")]
            results = orchestrator.run_multiple_models(ids_list, payload)
        else:
            results = orchestrator.run_all_compatible_models(payload)
            
        return {"comparisons": results}
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
''')
