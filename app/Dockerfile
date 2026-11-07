# Static site served by nginx. The "unprivileged" image runs as a non-root user on port 8080.
FROM nginxinc/nginx-unprivileged:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY site/ /usr/share/nginx/html/

# Set by the CI pipeline to the git commit (sha-xxxxxxx)
ARG APP_VERSION=dev

USER root
# /version endpoint + a small footer on the page showing which build is live
RUN printf '{"version":"%s"}\n' "$APP_VERSION" > /usr/share/nginx/html/version.json \
 && sed -i "s#</body>#<footer style=\"position:fixed;right:10px;bottom:6px;font:12px system-ui,sans-serif;opacity:.6\">${APP_VERSION} · deployed by GitHub Actions + Flux</footer></body>#" /usr/share/nginx/html/index.html \
 && chmod -R a+rX /usr/share/nginx/html
USER 101

EXPOSE 8080
