import dash
from dash import Dash, dcc, html, Input, Output, dash_table, State
import pandas as pd
import dash_bootstrap_components as dbc
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


# Obtener los datos iniciales de trabajadores
df_workers = fetch_workers_data()

# Crear la aplicación Dash con un tema de Bootstrap
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

# Layout de la aplicación
app.layout = html.Div(
    [
        # Encabezado
        dbc.NavbarSimple(
            children=[
                dbc.NavItem(dbc.NavLink("Home", href="/")),
                dbc.NavItem(dbc.NavLink("About", href="#")),
            ],
            brand="Workers Dashboard",
            brand_href="#",
            color="primary",
            dark=True,
        ),
        # Contenido Principal
        dbc.Container(
            [
                html.H2("Workers Status Table", className="text-center my-4"),
                dash_table.DataTable(
                    id="table",
                    columns=[
                        {"name": i.capitalize(), "id": i} for i in df_workers.columns
                    ],
                    data=df_workers.to_dict("records"),
                    row_selectable="single",
                    style_table={"overflowX": "auto"},
                    style_header={
                        "backgroundColor": "rgb(230, 230, 230)",
                        "fontWeight": "bold",
                        "textAlign": "center",
                    },
                    style_cell={
                        "textAlign": "center",
                        "padding": "10px",
                        "backgroundColor": "#f9f9f9",
                        "border": "1px solid #ddd",
                    },
                    style_data_conditional=[
                        {
                            "if": {"row_index": "odd"},
                            "backgroundColor": "rgb(248, 248, 248)",
                        }
                    ],
                ),
                dcc.Location(
                    id="url", refresh=False
                ),  # Para manejar la URL de la página
                html.Div(id="page-content"),  # Contenedor para los detalles de procesos
                # Inicializa los contenedores de las tablas vacías
                html.Div(
                    id="process-table-container",
                    children=[
                        dash_table.DataTable(
                            id="process_table"
                        )  # Placeholder inicial vacío
                    ],
                ),
                html.Div(
                    id="task-content",
                    children=[
                        dash_table.DataTable(
                            id="task_table"
                        )  # Placeholder inicial vacío
                    ],
                ),
            ],
            className="my-4",
        ),
        # Pie de página
        dbc.Container(
            dbc.Row(
                dbc.Col(
                    html.Footer(
                        "© 2024 Workers Dashboard - All Rights Reserved",
                        className="text-center my-4",
                    ),
                    width=12,
                )
            )
        ),
    ]
)


# Callback para manejar el clic en la fila de la tabla de trabajadores y redirigir a la URL de detalles
@app.callback(
    Output("url", "pathname"),
    Input("table", "selected_rows"),
    prevent_initial_call=True,
)
def update_url(selected_rows):
    if selected_rows:
        selected_id = df_workers.iloc[selected_rows[0]]["id"]
        return f"/details/{selected_id}"
    return dash.no_update


# Callback para mostrar la página de detalles con la tabla de procesos
@app.callback(
    Output("process-table-container", "children"),
    Input("url", "pathname"),
)
def display_processes(pathname):
    if pathname and pathname.startswith("/details/"):
        worker_id = pathname.split("/")[-1]
        df_process = fetch_process_data(worker_id)

        if df_process.empty:
            return html.Div(
                [
                    html.Br(),
                    html.H3(
                        f"No data found for Worker ID: {worker_id}",
                        className="text-center my-4",
                    ),
                    dbc.Button("Go back", href="/", color="primary", className="mt-4"),
                ],
                className="text-center",
            )

        # Actualiza el contenido del contenedor 'process-table-container'
        return dash_table.DataTable(
            id="process_table",
            columns=[{"name": i.capitalize(), "id": i} for i in df_process.columns],
            data=df_process.to_dict("records"),
            row_selectable="single",
            style_table={"overflowX": "auto"},
            style_header={
                "backgroundColor": "rgb(230, 230, 230)",
                "fontWeight": "bold",
                "textAlign": "center",
            },
            style_cell={
                "textAlign": "center",
                "padding": "10px",
                "backgroundColor": "#f9f9f9",
                "border": "1px solid #ddd",
            },
            style_data_conditional=[
                {
                    "if": {"row_index": "odd"},
                    "backgroundColor": "rgb(248, 248, 248)",
                }
            ],
        )
    return dash.no_update


# Callback para manejar el clic en la fila de la tabla de procesos y mostrar la tabla de tareas
@app.callback(
    Output("task-content", "children"),
    Input("process_table", "selected_rows"),
    State("process_table", "data"),
    prevent_initial_call=True,
)
def display_tasks(selected_rows, process_data):
    if selected_rows:
        process_id = process_data[selected_rows[0]]["id"]
        df_tasks = fetch_task_data(process_id)

        if df_tasks.empty:
            return html.Div(
                html.Br(),
                html.H3(
                    f"No tasks found for Process ID: {process_id}",
                    className="text-center my-4",
                ),
                className="text-center",
            )

        # Actualiza el contenido del contenedor 'task-content'
        return dash_table.DataTable(
            id="task_table",
            columns=[{"name": i.capitalize(), "id": i} for i in df_tasks.columns],
            data=df_tasks.to_dict("records"),
            style_table={"overflowX": "auto"},
            style_header={
                "backgroundColor": "rgb(230, 230, 230)",
                "fontWeight": "bold",
                "textAlign": "center",
            },
            style_cell={
                "textAlign": "center",
                "padding": "10px",
                "backgroundColor": "#f9f9f9",
                "border": "1px solid #ddd",
            },
            style_data_conditional=[
                {
                    "if": {"row_index": "odd"},
                    "backgroundColor": "rgb(248, 248, 248)",
                }
            ],
        )
    return dash.no_update


# Ejecutar la aplicación
if __name__ == "__main__":
    app.run_server(debug=True)
