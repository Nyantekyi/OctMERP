<template>
  <UApp>
    <NuxtLayout>
      <div class="shell">
        <NuxtRouteAnnouncer />

        <UContainer class="space-y-10">
          <section class="hero-grid">
            <div class="space-y-5">
              <UBadge color="primary" variant="subtle" size="lg">
                Nuxt UI v4.6.0
              </UBadge>

              <div class="space-y-4">
                <h1 class="headline">ERP frontend scaffold</h1>
                <p class="copy">
                  The Nuxt project is prepared with Nuxt UI components and a
                  tenant-aware server API layer.
                </p>
              </div>

              <div class="actions">
                <UButton
                  label="Open API health"
                  :to="healthUrl"
                  target="_blank"
                  size="xl"
                />
                <UButton
                  label="Nuxt UI docs"
                  to="https://ui.nuxt.com"
                  target="_blank"
                  color="neutral"
                  variant="outline"
                  size="xl"
                />
              </div>
            </div>

            <UCard class="status-card">
              <template #header>
                <div class="card-header">
                  <span class="card-title">Frontend status</span>
                  <UBadge color="success" variant="subtle">Ready</UBadge>
                </div>
              </template>

              <div class="space-y-4">
                <div>
                  <p class="meta-label">Health route</p>
                  <p class="meta-value">{{ healthUrl }}</p>
                </div>

                <USeparator />

                <div class="checklist">
                  <p>Nuxt UI module enabled</p>
                  <p>Starter shell rendered with UI components</p>
                  <p>Tenant-aware server routes configured</p>
                </div>
              </div>
            </UCard>
          </section>
        </UContainer>
      </div>
    </NuxtLayout>
  </UApp>
</template>

<script setup lang="ts">
const healthUrl = '/api/health'
</script>

<style scoped>
.shell {
  min-height: 100vh;
  padding: 4rem 1.5rem;
  background:
    radial-gradient(circle at top left, rgba(14, 165, 233, 0.18), transparent 32%),
    linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
  color: #0f172a;
  padding-top: 4rem;
  padding-bottom: 4rem;
}

.hero-grid {
  display: grid;
  gap: 2rem;
  align-items: start;
}

.headline {
  margin: 0;
  font-size: clamp(2.5rem, 6vw, 4.5rem);
  line-height: 0.95;
  letter-spacing: -0.04em;
}

.copy {
  max-width: 42rem;
  font-size: 1.05rem;
  line-height: 1.7;
  color: #334155;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.status-card {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
}

.meta-label {
  margin: 0 0 0.35rem;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #475569;
}

.meta-value {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  word-break: break-all;
}

.checklist {
  display: grid;
  gap: 0.75rem;
  color: #334155;
}

.checklist p {
  margin: 0;
}

@media (min-width: 960px) {
  .hero-grid {
    grid-template-columns: minmax(0, 1.6fr) minmax(320px, 0.9fr);
  }
}
</style>
