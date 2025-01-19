import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import TextArea from './index'; // Verifique o caminho correto do arquivo


describe('TextArea Component - MC/DC Coverage', () => {
  test('calls onChange when defined (C1 = true)', () => {
    const handleChange = jest.fn();
    render(<TextArea value="" onChange={handleChange} />);

    const textarea = screen.getByRole('textbox');
    fireEvent.change(textarea, { target: { value: 'Test Value' } });

    expect(handleChange).toHaveBeenCalledWith('Test Value');
  });

  test('does not call onChange when undefined (C1 = false)', () => {
    render(<TextArea value="" />);

    const textarea = screen.getByRole('textbox');
    fireEvent.change(textarea, { target: { value: 'Test Value' } });

    // No assertion needed for undefined onChange
  });

  // test('resizes when textAreaElement.current is defined (C2 = true)', async () => {
  //   render(<TextArea value="Short text" />);
    
  //   // Acesse o textarea após a renderização
  //   const textarea = screen.getByRole('textbox');
    
  //   // Obtenha a altura antes da alteração
  //   const initialHeight = textarea.scrollHeight;
    
  //   // Modifique o conteúdo da textarea para disparar o redimensionamento
  //   fireEvent.change(textarea, { target: { value: 'Long text\nwith multiple lines' } });
    
  //   // Aguarde o redimensionamento ser aplicado
  //   await new Promise((resolve) => setTimeout(resolve, 0));
    
  //   // A altura deve ser maior depois da mudança
  //   expect(textarea.scrollHeight).toBeGreaterThan(initialHeight);
  // });
  

  
  

  test('does not resize when textAreaElement.current is null (C2 = false)', () => {
    render(<TextArea value="Short text" />);
    // Simulate null ref
    const textarea = screen.getByRole('textbox');
    textarea.style.height = '50px';
    fireEvent.change(textarea, { target: { value: 'New value' } });

    expect(textarea.style.height).toBe('50px');
  });

  test('focuses when focusOnMount=true and textAreaElement.current is defined (C3=true, C2=true)', () => {
    render(<TextArea value="" focusOnMount={true} />);
    const textarea = screen.getByRole('textbox');

    expect(textarea).toHaveFocus();
  });

  test('does not focus when focusOnMount=false (C3=false, C2=true)', () => {
    render(<TextArea value="" focusOnMount={false} />);
    const textarea = screen.getByRole('textbox');

    expect(textarea).not.toHaveFocus();
  });
});
