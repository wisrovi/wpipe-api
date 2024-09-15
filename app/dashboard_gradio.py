import gradio as gr
import pandas as pd
import requests

# URLs de las APIs
API_WORKERS_URL = "http://localhost:8418/dashboard_workers"
API_PROCESS_URL = "http://localhost:8418/dashboard_process"
API_TASK_URL = "http://localhost:8418/dashboard_tasks"

# Función para obtener los datos desde la API de trabajadores
def fetch_workers_data():
    try:
        response = requests.get(API_WORKERS_URL)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data)
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener datos de la API: {e}")
        return pd.DataFrame([])

# Función para obtener los datos desde la API de procesos
def fetch_process_data(worker_id):
    try:
        response = requests.get(f"{API_PROCESS_URL}/{worker_id}")
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data)
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener datos de la API de procesos: {e}")
        return pd.DataFrame([])

# Función para obtener los datos desde la API de tareas
def fetch_task_data(process_id):
    try:
        response = requests.get(f"{API_TASK_URL}/{process_id}")
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data)
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener datos de la API de tareas: {e}")
        return pd.DataFrame([])

# Función para obtener los IDs de trabajadores
def get_worker_ids():
    df = fetch_workers_data()
    return df['id'].tolist()

# Función para obtener los IDs de procesos para un trabajador específico
def get_process_ids(worker_id):
    df = fetch_process_data(worker_id)
    return df['id'].tolist() if not df.empty else []

# Función para obtener los IDs de tareas para un proceso específico
def get_task_ids(process_id):
    df = fetch_task_data(process_id)
    return df['id'].tolist() if not df.empty else []

# Función para actualizar las tablas
def update_tables(worker_id=None, process_id=None):
    workers_df = fetch_workers_data()
    processes_df = fetch_process_data(worker_id) if worker_id else pd.DataFrame()
    tasks_df = fetch_task_data(process_id) if process_id else pd.DataFrame()
    return workers_df, processes_df, tasks_df

# Función para crear la interfaz en Gradio
def create_interface():
    with gr.Blocks() as demo:
        with gr.Row():
            gr.Markdown("# Workers Table")
            workers_table = gr.DataFrame(value=fetch_workers_data(), interactive=True)
        
        with gr.Row():
            gr.Markdown("# Process Table")
            processes_table = gr.DataFrame(value=pd.DataFrame(), interactive=True, visible=False)
        
        with gr.Row():
            gr.Markdown("# Task Table")
            tasks_table = gr.DataFrame(value=pd.DataFrame(), interactive=True, visible=False)

        # Dropdowns
        worker_select = gr.Dropdown(label="Select Worker", choices=get_worker_ids())
        process_select = gr.Dropdown(label="Select Process", choices=[])
        task_select = gr.Dropdown(label="Select Task", choices=[])

        # Botón de actualización
        refresh_button = gr.Button("Refresh Data")

        # Callbacks
        def on_worker_select(worker_id):
            processes_df = fetch_process_data(worker_id)
            process_ids = get_process_ids(worker_id)
            return processes_df, process_ids

        def on_process_select(process_id):
            tasks_df = fetch_task_data(process_id)
            task_ids = get_task_ids(process_id)
            return tasks_df, task_ids

        def refresh():
            workers_df, processes_df, tasks_df = update_tables(
                worker_select.value if worker_select.value else None,
                process_select.value if process_select.value else None
            )
            return workers_df, processes_df, tasks_df

        # Conectar los callbacks
        worker_select.change(on_worker_select, inputs=worker_select, outputs=[processes_table, process_select])
        process_select.change(on_process_select, inputs=process_select, outputs=[tasks_table, task_select])
        refresh_button.click(refresh, outputs=[workers_table, processes_table, tasks_table])

    return demo

if __name__ == "__main__":
    demo = create_interface()
    demo.launch()
