<script setup lang="ts">
defineShortcuts({
  'g-h': () => navigateTo('/')
})
</script>

<template>
  <div class="relative min-h-screen overflow-hidden bg-auth-surface">
    <div class="pointer-events-none absolute -left-24 top-0 h-80 w-80 rounded-full bg-teal-400/25 blur-3xl" />
    <div class="pointer-events-none absolute -right-20 bottom-0 h-72 w-72 rounded-full bg-cyan-400/25 blur-3xl" />

    <div class="relative grid min-h-screen grid-cols-1 lg:grid-cols-2">
      <section class="flex items-center justify-center p-6 sm:p-10">
        <div class="w-full max-w-md">
          <slot />
        </div>
      </section>

      <section class="hidden border-l border-default/40 bg-gradient-to-br from-teal-600/90 via-cyan-700/80 to-slate-900 text-white lg:flex lg:flex-col lg:justify-end lg:p-12">
        <p class="text-sm uppercase tracking-[0.2em] text-white/80">
          Pharmaceutical Operations
        </p>
        <h2 class="mt-3 text-3xl font-semibold leading-tight">
          One platform for inventory, compliance, finance, and workforce.
        </h2>
        <p class="mt-4 max-w-md text-sm text-white/80">
          Use secure role-based access to coordinate data and decisions across every unit in the enterprise.
        </p>
      </section>
    </div>
  </div>
</template>

<style scoped></style>
