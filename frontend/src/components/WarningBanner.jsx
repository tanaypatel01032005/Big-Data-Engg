import React from "react";

export default function WarningBanner({ message, onHide }) {
    if (!message) return null;

    return (
        <div className="warning-banner slide-down">
            <div className="warning-content">
                <span className="warning-icon">⚠️</span>
                <span className="warning-text">{message}</span>
            </div>
            {onHide && (
                <button className="warning-close" onClick={onHide}>
                    &times;
                </button>
            )}
        </div>
    );
}
