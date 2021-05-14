/* eslint-disable react/prop-types */

import React from 'react';

import Icon from './common/Icon';

export interface ModuleRenderContext {
    currentPath: string;
    collapsed: boolean;
    navigate(url: string): Promise<void>;
}

export interface ModuleDefinition {
    render(context: ModuleRenderContext): React.ReactFragment;
}

export interface SidebarProps {
    modules: ModuleDefinition[];
    currentPath: string;
    navigate(url: string): Promise<void>;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const usePersistedState = <T, _>(key: string, defaultValue: T): [T, (value: T) => void]  => {
  const value = localStorage.getItem(key);
  const [state, setState] = React.useState(
    value ? JSON.parse(value) : defaultValue
  );
  React.useEffect(() => {
    localStorage.setItem(key, JSON.stringify(state));
  }, [key, state]);
  return [state, setState];
};

export const Sidebar: React.FunctionComponent<SidebarProps> =  ({ modules, currentPath, navigate }) => {
  const [collapsed, setCollapsed] = usePersistedState('wagtail-sidebar-collapsed', window.innerWidth < 800);

  const onClickCollapseToggle = (e: React.MouseEvent) => {
    e.preventDefault();
    setCollapsed(!collapsed);
  };

  const renderedModules = modules.map(module => module.render({ collapsed, navigate, currentPath }));

  return (
    <aside className={'sidebar' + (collapsed ? ' sidebar--collapsed' : '')}>
      <div className="sidebar__inner">
        <button onClick={onClickCollapseToggle} className="button sidebar__collapse-toggle">
          {collapsed ? <Icon name="angle-double-right" /> : <Icon name="angle-double-left" />}
        </button>

        {renderedModules}
      </div>
    </aside>
  );
};
