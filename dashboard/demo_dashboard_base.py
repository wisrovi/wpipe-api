import os
import dash
from dash import Dash, dcc, html, Input, Output, dash_table, State
import pandas as pd
import dash_bootstrap_components as dbc
import requests


BACKEND = os.environ.get("BACKEND")

API_WORKERS_URL = f"http://{BACKEND}/dashboard_workers"
API_PROCESS_URL = f"http://{BACKEND}/dashboard_process"
API_TASK_URL = f"http://{BACKEND}/dashboard_tasks"


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
        df_process = pd.DataFrame(data)
        # Ordenar por Status (Errores primero) y luego por Last_update (más reciente primero)
        df_process["Status"] = pd.Categorical(
            df_process["status"],
            categories=["error", "running", "pending", "success"],
            ordered=True,
        )
        df_process = df_process.sort_values(
            by=["Status", "last_update"], ascending=[True, False]
        )
        return df_process
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener datos de la API de procesos: {e}")
        return pd.DataFrame([])


# Función para obtener los datos desde la API de tareas
def fetch_task_data(process_id):
    try:
        response = requests.get(f"{API_TASK_URL}/{process_id}")
        response.raise_for_status()
        data = response.json()

        df_task = pd.DataFrame(data)
        df_task["State"] = pd.Categorical(
            df_task["State"],
            categories=["success", "running", "pending"],
            ordered=True,
        )
        df_task = df_task.sort_values(by=["Step", "State"], ascending=[True, False])

        return df_task
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener datos de la API de tareas: {e}")
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


# Crear la aplicación Dash con un tema de Bootstrap
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

# Layout de la aplicación
app.layout = html.Div(
    [
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
        dbc.Container(
            [
                html.H2("Workers Status Table", className="text-center my-4"),
                dcc.Location(
                    id="url", refresh=False
                ),  # Para manejar la URL de la página
                html.H3(
                    "Workers Status Table", className="text-center"
                ),  # Título de la tabla de trabajadores
                dcc.Interval(
                    id="interval-workers", interval=15 * 1000, n_intervals=0
                ),  # Intervalo de 15 segundos
                dash_table.DataTable(
                    id="table",
                    columns=[],  # Las columnas se establecerán dinámicamente
                    data=[],  # Los datos se establecerán dinámicamente
                    row_selectable="single",
                    filter_action="native",  # Permitir filtrado en la tabla
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
                    page_size=10,  # Paginación con 10 filas por página
                ),
                html.Div(id="page-content"),  # Contenedor para los detalles de procesos
                html.H3(
                    "Processes Table", className="text-center mt-4"
                ),  # Título de la tabla de procesos
                dcc.Store(id="process-filter-store", data={"filter_query": ""}),
                dcc.Store(id="task-filter-store", data={"filter_query": ""}),
                dcc.Interval(
                    id="interval-processes", interval=15 * 1000, n_intervals=0
                ),  # Intervalo de 15 segundos
                html.Div(
                    id="process-table-container",
                    children=[
                        dash_table.DataTable(
                            id="process_table",
                            page_size=10,  # Paginación con 10 filas por página
                        )
                    ],
                ),
                html.H3(
                    "Tasks Table", className="text-center mt-4"
                ),  # Título de la tabla de tareas
                dcc.Interval(
                    id="interval-tasks", interval=15 * 1000, n_intervals=0
                ),  # Intervalo de 15 segundos
                html.Div(
                    id="task-content",
                    children=[
                        dash_table.DataTable(
                            id="task_table",
                            page_size=10,  # Paginación con 10 filas por página
                        )
                    ],
                ),
            ],
            className="my-4",
        ),
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


# Callback para actualizar la tabla de trabajadores cada 15 segundos
@app.callback(
    [Output("table", "data"), Output("table", "columns")],
    [Input("interval-workers", "n_intervals")],
)
def refresh_workers_table(_):
    df_workers = fetch_workers_data()
    data = df_workers.to_dict("records")
    columns = [{"name": i.capitalize(), "id": i} for i in df_workers.columns]
    return data, columns


# Callback para manejar el clic en la fila de la tabla de trabajadores y redirigir a la URL de detalles
@app.callback(
    Output("url", "pathname"),
    Input("table", "selected_rows"),
    prevent_initial_call=True,
)
def update_url(selected_rows):
    df_workers = fetch_workers_data()  # Volver a cargar los datos
    if selected_rows:
        selected_id = df_workers.iloc[selected_rows[0]]["id"]
        return f"/details/{selected_id}"
    return dash.no_update


# Callback para mostrar la página de detalles con la tabla de procesos
@app.callback(
    Output("process-table-container", "children"),
    [Input("url", "pathname"), Input("interval-processes", "n_intervals")],
)
def display_processes(pathname, _):
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

        return dash_table.DataTable(
            id="process_table",
            columns=[{"name": i.capitalize(), "id": i} for i in df_process.columns],
            data=df_process.to_dict("records"),
            row_selectable="single",
            filter_action="native",  # Permitir filtrado en la tabla
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
            page_size=10,  # Paginación con 10 filas por página
        )
    return dash.no_update


# Callback para manejar el clic en la fila de la tabla de procesos y mostrar la tabla de tareas
@app.callback(
    Output("task-content", "children"),
    [Input("process_table", "selected_rows"), Input("interval-tasks", "n_intervals")],
    State("process_table", "data"),
    prevent_initial_call=True,
)
def display_tasks(selected_rows, _, process_data):
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

        return dash_table.DataTable(
            id="task_table",
            columns=[{"name": i.capitalize(), "id": i} for i in df_tasks.columns],
            data=df_tasks.to_dict("records"),
            filter_action="native",  # Permitir filtrado en la tabla
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
            page_size=10,  # Paginación con 10 filas por página
        )
    return dash.no_update


@app.callback(
    Output("process-filter-store", "data"), Input("process_table", "filter_query")
)
def update_process_filter(filter_query):
    return {"filter_query": filter_query}


@app.callback(Output("task-filter-store", "data"), Input("task_table", "filter_query"))
def update_task_filter(filter_query):
    return {"filter_query": filter_query}


# Ejecutar la aplicación
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)
