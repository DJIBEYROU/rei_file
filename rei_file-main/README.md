### Backend: Flask
1. Navigate to the server folder. Create a Python virtual environment where the dependencies for this project will be installed.
```
cd server
python3 -m venv venv
```

2. Activate the environment and install all the packages available in the requirement.txt file.
```
source venv/bin/activate
pip install -r ./requirements.txt
```
npm
4. Run the server
```
flask run -h localhost -p 3000
```

### Frontend: Svelte
1. Open a new terminal tab and navigate to the client folder. Install the dependencies
```
cd client
npm install
```

2. Run the command below to build the app and have the Vite build tool watch for changes
```
npm run autobuild
```

3. View the app on `http://localhost:3000/`
