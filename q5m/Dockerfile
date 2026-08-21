FROM nginxinc/nginx-unprivileged:1.29.1-alpine@sha256:27985295bdb22a1ef8f712863210bd5877c0f3006494a593e86b3fe0fa55467e

ARG Q5M_RELEASE
USER root
COPY q5m/nginx.conf /etc/nginx/nginx.conf
COPY --chmod=0555 q5m/health.sh /usr/local/bin/erdos-193-health
COPY viz/ /usr/share/nginx/html/
RUN test "${#Q5M_RELEASE}" -eq 40 \
    && case "$Q5M_RELEASE" in *[!0-9a-f]*) exit 1 ;; *) : ;; esac \
    && printf '%s\n' "$Q5M_RELEASE" > /usr/share/nginx/html/.q5m-release \
    && chmod -R a+rX,a-w /etc/nginx/nginx.conf /usr/local/bin/erdos-193-health /usr/share/nginx/html
USER 1000:1000

EXPOSE 8193
ENTRYPOINT ["nginx", "-g", "daemon off;"]
