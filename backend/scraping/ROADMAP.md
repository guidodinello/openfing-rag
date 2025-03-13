-   [ ] Usar una base de datos en vez de crearse la propia en base a archivos de texto? Podemos tener para cada curso acronimo, nombre completo, para cada clase curso al que pertenece, url, etc.
-   [ ] Definir un formato de transcripcion y no tener 4 distintos. json o txt?
-   [ ] Arreglar la concurrencia. Hay hilos en el main que llaman a downloader que spawnean mas hilos adentro. es dificil de seguir, ademas que whisper no es thread safe y ademas el GIL.

-   [ ] Usar un code style standard de python. https://peps.python.org/pep-0008/, algun formatter, Black o Ruff?
-   [ ] Si hacemos test unitarios en algun momento. pytest?
-   [ ] pylint y mypy para chequear errores de codigo?

-   [ ] Podemos usar Prefect [GitHub - PrefectHQ/prefect: Prefect is a workflow orchestration framework for building resilient data pipelines in Python.](https://github.com/PrefectHQ/prefect), no tenemos que manejar la concurrencia a mano, ni el setup del cronjob. ademas de otras utilidades como retry para las requests, logging, etc.
