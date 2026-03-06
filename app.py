def gestion_github(file_path, data=None, sha=None, methode="GET"):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    if methode == "GET":
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            res = r.json()
            content = json.loads(base64.b64decode(res['content']).decode('utf-8'))
            return content, res['sha']
        return None, None

    elif methode == "PUT":
        content_encoded = base64.b64encode(json.dumps(data, indent=4).encode('utf-8')).decode('utf-8')
        payload = {"message": "Ajout POI", "content": content_encoded, "branch": BRANCH}
        if sha: payload["sha"] = sha
        
        r = requests.put(url, json=payload, headers=headers)
        
        # --- LE DEBUG QUI SAUVE ---
        if r.status_code not in [200, 201]:
            st.error(f"Code Erreur GitHub : {r.status_code}")
            st.json(r.json()) # Affiche la raison exacte (ex: "Resource protected by organziation")
            
        return r.status_code in [200, 201]
