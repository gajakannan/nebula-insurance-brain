FROM brain-f0005-engine:2026-10-25-4020923b AS engine-build
USER root
COPY engine /app/brain/engine
RUN uv sync --locked --directory /app/brain/engine

FROM brain-f0005-engine:2026-10-25-4020923b AS engine-runtime
COPY --from=engine-build /opt/venv /opt/venv
COPY --from=engine-build /app/brain/engine /app/brain/engine
USER 1000:1000

FROM brain-f0005-neuron:2026-10-25-4020923b AS neuron-build
USER root
COPY engine /app/brain/engine
COPY neuron /app/brain/neuron
RUN uv sync --locked --directory /app/brain/neuron

FROM brain-f0005-neuron:2026-10-25-4020923b AS neuron-runtime
COPY --from=neuron-build /opt/venv /opt/venv
COPY --from=neuron-build /app/brain/engine /app/brain/engine
COPY --from=neuron-build /app/brain/neuron /app/brain/neuron
USER 1000:1000
