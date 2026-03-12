<script setup lang="ts">
definePageMeta({
  layout: 'auth'
})

useSeoMeta({
  title: 'Sign In',
  description: 'Authenticate into the pharmaceutical ERP system.'
})
</script>

<template>
  <FormsAuthSignIn />
</template>

<style scoped></style>
