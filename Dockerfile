FROM codecontinuum/ddj

LABEL maintainer="sxzdhu"

# COPY cca /opt/cca/
RUN set -x && \
    rm -rf /opt/cca/ddutil && \
    rm -rf /opt/cca/esecfse2018 && \
    rm -rf /opt/cca/regression_examples && \
    pip install networkx && \
    pip install tabulate

COPY ddutil /opt/cca/ddutil

CMD ["/bin/bash"]
