import React from "react";
import styled from "styled-components";

const AestheticButton = ({ children, onClick, disabled }) => {
  return (
    <StyledWrapper>
      <button className="btn" onClick={onClick} disabled={disabled}>
        <i className="animation" />
        {children}
        <i className="animation" />
      </button>
    </StyledWrapper>
  );
};

const StyledWrapper = styled.div`
  .btn {
    outline: 0;
    display: inline-flex;
    align-items: center;
    justify-content: space-between;
    background: #40b3a2;
    min-width: 200px;
    border: 0;
    border-radius: 4px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    box-sizing: border-box;
    padding: 16px 20px;
    color: #fff;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    overflow: hidden;
    cursor: pointer;
    transition: opacity 0.3s ease-in-out;
  }

  .btn:hover {
    opacity: 0.95;
  }

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn .animation {
    border-radius: 100%;
    animation: ripple 0.6s linear infinite;
  }

  @keyframes ripple {
    0% {
      box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.1),
        0 0 0 20px rgba(255, 255, 255, 0.1),
        0 0 0 40px rgba(255, 255, 255, 0.1),
        0 0 0 60px rgba(255, 255, 255, 0.1);
    }

    100% {
      box-shadow: 0 0 0 20px rgba(255, 255, 255, 0.1),
        0 0 0 40px rgba(255, 255, 255, 0.1),
        0 0 0 60px rgba(255, 255, 255, 0.1),
        0 0 0 80px rgba(255, 255, 255, 0);
    }
  }
`;

export default AestheticButton;
