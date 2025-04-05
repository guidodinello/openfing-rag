import React, { ReactNode } from 'react';

export const ListComponent: React.FC<{array: ReactNode[], onItemClick: (item: ReactNode) => void}> = ({array, onItemClick}) => {
    return (
        <div>
            {array.map((item:ReactNode, index:number) => (
                <button type={'button'}  key={index} onClick={() => onItemClick(item)}>
                    {item} 
                </button>
            ))}
        </div>
    )
}