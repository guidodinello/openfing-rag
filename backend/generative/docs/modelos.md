
### LLMs Open Source

Hay varias opciones viables dependiendo de tus recursos:

1. **Mistral 7B**
- Excelente balance rendimiento/recursos
- ~16GB VRAM para inferencia
- Muy buena calidad de respuestas
- Tiene versiones optimizadas (llamadas "mixtures")

2. **Llama-2 7B**
- Similar requerimientos a Mistral
- Bien documentado
- Gran comunidad
- Buenos fine-tunes disponibles

3. **Phi-2 (2.7B)**
- Muy eficiente (4-8GB VRAM)
- Sorprendentemente capaz para su tamaño
- Ideal para recursos limitados
- Microsoft lo optimizó específicamente para casos académicos

4. **Tinyllama (1.1B)**
- Ultrapequeno (2-4GB VRAM)
- Calidad decente para Q&A simple
- No tan bueno para generación compleja

**Recomendación para tu caso**:
1. Empezaría con Phi-2 o Mistral 7B
2. Usar quantización para reducir requerimientos
3. Considerar vllm o text-generation-inference para inferencia eficiente
4. Si los recursos son muy limitados, TinyLlama podría funcionar
