export function useDashboard() {
  const isSidebarCollapsed = useState('dashboard:sidebar-collapsed', () => false)
  const isNotificationsSlideoverOpen = useState('dashboard:notifications-open', () => false)

  const toggleSidebar = (next?: boolean) => {
    if (typeof next === 'boolean') {
      isSidebarCollapsed.value = next
      return
    }

    isSidebarCollapsed.value = !isSidebarCollapsed.value
  }

  watch(() => useRoute().fullPath, () => {
    isNotificationsSlideoverOpen.value = false
  })

  return {
    isSidebarCollapsed,
    isNotificationsSlideoverOpen,
    toggleSidebar
  }
}
