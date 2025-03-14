import React from "react";
import styled from "styled-components";

const ModeToggle = ({ isManualMode, onToggle }) => {
  return (
    <StyledWrapper>
      <label className="rocker rocker-small">
        <input type="checkbox" checked={!isManualMode} onChange={onToggle} />
        <span className="switch-left">Auto</span>
        <span className="switch-right">Man</span>
      </label>
    </StyledWrapper>
  );
};

const StyledWrapper = styled.div`
  .rocker {
    display: inline-block;
    position: relative;
    font-size: 2em;
    font-weight: bold;
    text-align: center;
    text-transform: uppercase;
    color: #888;
    width: 9em;
    height: 4em;
    overflow: hidden;
    border-bottom: 0.5em solid #eee;
  }

  .rocker-small {
    font-size: 0.75em;
    margin: 1em;
  }

  .rocker::before {
    content: "";
    position: absolute;
    top: 0.5em;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #999;
    border: 0.5em solid #eee;
    border-bottom: 0;
  }

  .rocker input {
    opacity: 0;
    width: 0;
    height: 0;
  }

  .switch-left,
  .switch-right {
    cursor: pointer;
    position: absolute;
    display: flex;
    align-items: center;
    justify-content: center;
    height: 2.5em;
    width: 4em;
    transition: 0.2s;
    user-select: none;
  }

  .switch-left {
    height: 2.4em;
    width: 3.5em;
    left: 0.85em;
    bottom: 0.4em;
    background-color: #ddd;
    transform: rotate(15deg) skewX(15deg);
  }

  .switch-right {
    right: 0.5em;
    bottom: 0;
    background-color: #0084d0;
    color: #fff;
  }

  .switch-left::before,
  .switch-right::before {
    content: "";
    position: absolute;
    width: 0.4em;
    height: 2.45em;
    bottom: -0.45em;
    background-color: #ccc;
    transform: skewY(-65deg);
  }

  .switch-left::before {
    left: -0.4em;
  }

  .switch-right::before {
    right: -0.375em;
    background-color: transparent;
    transform: skewY(65deg);
  }

  input:checked + .switch-left {
    background-color: #bd5757;
    color: #fff;
    bottom: 0px;
    left: 0.5em;
    height: 2.5em;
    width: 4em;
    transform: rotate(0deg) skewX(0deg);
  }

  input:checked + .switch-left::before {
    background-color: transparent;
    width: 3.5em;
  }

  input:checked + .switch-left + .switch-right {
    background-color: #ddd;
    color: #888;
    bottom: 0.4em;
    right: 0.8em;
    height: 2.4em;
    width: 3.5em;
    transform: rotate(-15deg) skewX(-15deg);
  }

  input:checked + .switch-left + .switch-right::before {
    background-color: #ccc;
  }

  input:focus + .switch-left {
    color: #333;
  }

  input:checked:focus + .switch-left {
    color: #fff;
  }

  input:focus + .switch-left + .switch-right {
    color: #fff;
  }

  input:checked:focus + .switch-left + .switch-right {
    color: #333;
  }
`;

export default ModeToggle;
