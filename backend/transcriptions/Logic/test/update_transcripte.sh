#!/bin/bash

ACRONYMS=("redes-2020" "redes-2021" "redes-2022" "redes-2024")
CLASS_NUMBERS=(4 5 6 7 8 9 10 11 12 13 14 15 16 16 17 18 19) # Add or change class numbers as needed

for ACRONYM in "${ACRONYMS[@]}"; do
  for CLASS in "${CLASS_NUMBERS[@]}"; do
    curl --location --request PUT "localhost:8001/transcribe/${ACRONYM}/${CLASS}" \
      --header 'Accept: application/json' \
      --header 'Content-Type: application/json' \
      --data '{
        "model_size": "medium",
        "language": "es"
      }'
    echo # Print a newline for readability
  done
done