import React, { ReactElement } from "react";

import { Navbar } from "../../common/navbar/navbar";
import { Sidebar } from "../../common/sidebar/sidebar";

enum LayoutType {
  // Add more layout types here
  Default = "Default",
  NavAndSidebar = "NavAndSidebar",
  Nav = "Nav",
}

type LayoutProps = {
  children: React.ReactNode;
  layoutType: LayoutType;
};

const Layout = ({ layoutType, children }: LayoutProps): ReactElement | null => {
  if (layoutType === LayoutType.Default) {
    return <div>{children}</div>;
  }
  if (layoutType === LayoutType.NavAndSidebar) {
    return (
      <div className="flex min-h-screen">
        <Sidebar />
        <div className="flex-1 flex flex-col">
          <Navbar />
          <main className="flex-1 p-4">{children}</main>
        </div>
      </div>
    );
  }
  if (layoutType === LayoutType.Nav) {
    return (
      <>
        <Navbar />
        {children}
      </>
    );
  }
  return null;
};

export { Layout, LayoutType };
