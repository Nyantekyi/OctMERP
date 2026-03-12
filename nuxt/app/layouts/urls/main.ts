import type { NavigationMenuItem } from '@nuxt/ui'

export function getMainNavigation(activePath: string): NavigationMenuItem[][] {
  return [
    [
      {
        label: 'Dashboard',
        icon: 'i-lucide-layout-dashboard',
        to: '/',
        active: activePath === '/'
      },
      {
        label: 'Inventory',
        icon: 'i-lucide-package-search',
        to: '/inventory',
        active: activePath.startsWith('/inventory')
      },
      {
        label: 'Sales',
        icon: 'i-lucide-chart-line',
        to: '/sales',
        active: activePath.startsWith('/sales')
      }
    ],
    [
      {
        label: 'HR',
        icon: 'i-lucide-users-round',
        to: '/hr',
        active: activePath.startsWith('/hr')
      },
      {
        label: 'Logistics',
        icon: 'i-lucide-truck',
        to: '/logistics',
        active: activePath.startsWith('/logistics')
      },
      {
        label: 'Settings',
        icon: 'i-lucide-settings-2',
        to: '/settings',
        active: activePath.startsWith('/settings')
      }
    ]
  ]
}
