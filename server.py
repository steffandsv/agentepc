from flask import Flask, render_template, request, redirect, jsonify
import os
from core.state import StateManager

app = Flask(__name__)
manager = StateManager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/objective', methods=['POST'])
def set_objective():
    objective = request.form.get('objective')
    if objective:
        manager.set_objective(objective)
    return redirect('/')

@app.route('/stop')
def stop_agent():
    manager.clear_objective()
    manager.update_status("STOPPED", "Stopped by Web User")
    return redirect('/')

@app.route('/api/status')
def get_status():
    state = manager.get_state()
    return jsonify({
        "status": state.status,
        "objective": state.objective,
        "last_log": state.last_log,
        "last_updated": state.last_updated
    })

if __name__ == '__main__':
    # Ensure static dir exists
    if not os.path.exists('static'):
        os.makedirs('static')

    print("Starting Web Server on port 8000...")
    app.run(host='0.0.0.0', port=8000)
