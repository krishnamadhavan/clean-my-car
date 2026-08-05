import type { ThemeConfig } from 'ant-design-vue/es/config-provider/context'

/**
 * Clean My Car ops brand palette.
 *
 * Primary:  #4B49AC (main), #98BDFF (soft / highlights)
 * Secondary: #7DA0FA, #7978E9, #F3797E
 */
export const brandColors = {
  primary: '#4B49AC',
  primarySoft: '#98BDFF',
  secondary: '#7DA0FA',
  secondaryAlt: '#7978E9',
  accent: '#F3797E',
} as const

export const opsTheme: ThemeConfig = {
  token: {
    colorPrimary: brandColors.primary,
    colorInfo: brandColors.secondary,
    colorLink: brandColors.primary,
    colorSuccess: '#52c41a',
    colorWarning: brandColors.secondaryAlt,
    colorError: brandColors.accent,
    colorPrimaryBg: '#EEF0FF',
    colorPrimaryBgHover: brandColors.primarySoft,
    colorPrimaryBorder: brandColors.primarySoft,
    colorPrimaryHover: brandColors.secondaryAlt,
    colorPrimaryActive: '#3d3c8f',
    colorInfoBg: '#EAF1FF',
    colorInfoBorder: brandColors.secondary,
    borderRadius: 8,
    fontFamily:
      "Inter, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
    controlHeight: 36,
  },
  components: {
    Layout: {
      headerBg: brandColors.primary,
      headerColor: '#ffffff',
      headerHeight: 56,
      bodyBg: '#f5f7fb',
      siderBg: '#ffffff',
      triggerBg: brandColors.primary,
    },
    Menu: {
      itemSelectedBg: '#EEF0FF',
      itemSelectedColor: brandColors.primary,
      itemHoverBg: '#F3F5FF',
      itemHoverColor: brandColors.primary,
      itemActiveBg: '#E8EBFF',
    },
    Button: {
      primaryShadow: '0 2px 0 rgba(75, 73, 172, 0.12)',
      defaultBorderColor: brandColors.primarySoft,
    },
    Table: {
      headerBg: '#F0F3FF',
      headerColor: brandColors.primary,
      rowHoverBg: '#F8F9FF',
    },
    Card: {
      headerBg: 'transparent',
    },
    Tag: {
      defaultBg: '#EEF0FF',
      defaultColor: brandColors.primary,
    },
  },
}
