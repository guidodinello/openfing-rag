0. Login
```
uvx prefect-cloud login
```

1. Schedule flow run
```
❯ uv run src/openfing_audio_dl/prefect_integration.py

Your flow 'download-flow' is being served and polling for scheduled runs!

To trigger a run for this flow, use the following command:

        $ prefect deployment run 'download-flow/scheduled-downloader'

You can also run your flow via the Prefect UI: https://app.prefect.cloud/account/4856e295-dd17-4cc8-a176-f040fe83e4fa/workspace/4122af19-eb70-4c2b-bbab-24bbea13d3bd/deployments/deployment/ccf820c1-1105-4108-8617-08e1cdf3d04b

```
