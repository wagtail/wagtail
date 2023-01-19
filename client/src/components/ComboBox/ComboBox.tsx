import React, { useEffect, useState } from 'react';
import {
  useCombobox,
  UseComboboxStateChange,
  UseComboboxStateChangeTypes,
} from 'downshift';

import { gettext } from '../../utils/gettext';
import Icon from '../Icon/Icon';

import findMatches from './findMatches';

export const comboBoxTriggerLabel = gettext('Insert a block');
export const comboBoxLabel = gettext('Search options…');
export const comboBoxNoResults = gettext('No results');

export interface ComboBoxCategory<ItemType> {
  type: string;
  label: string | null;
  items: ItemType[];
}

export interface ComboBoxItem {
  type?: string;
  label?: string | null;
  description?: string | null;
  icon?: string | JSX.Element | null;
  category?: string;
  render?: (props: { option: ComboBoxItem }) => JSX.Element | string;
}

export { UseComboboxStateChange };

export type ComboBoxStateChange = UseComboboxStateChange<ComboBoxItem>;

export interface ComboBoxProps<ComboBoxOption> {
  label?: string;
  placeholder?: string;
  inputValue?: string;
  items: ComboBoxCategory<ComboBoxOption>[];
  getItemLabel: (
    type: string | undefined,
    item: ComboBoxOption,
  ) => string | null | undefined;
  getItemDescription: (item: ComboBoxOption) => string | null | undefined;
  getSearchFields: (item: ComboBoxOption) => (string | null | undefined)[];
  onSelect: (change: UseComboboxStateChange<ComboBoxOption>) => void;
  noResultsText?: string;
}

/**
 * Generic ComboBox component built with downshift, with a 2-column layout.
 */
export default function ComboBox<ComboBoxOption extends ComboBoxItem>({
  label,
  placeholder,
  inputValue,
  items,
  getItemLabel,
  getItemDescription,
  getSearchFields,
  onSelect,
  noResultsText,
}: ComboBoxProps<ComboBoxOption>) {
  // If there is no label defined, we treat the combobox as not needing its own field.
  const inlineCombobox = !label;
  const flatItems = items.flatMap<ComboBoxOption>(
    (category) => category.items || [],
  );
  const [inputItems, setInputItems] = useState<ComboBoxOption[]>(flatItems);
  // Re-create the categories so the two-column layout flows as expected.
  const categories = items.reduce<ComboBoxCategory<ComboBoxOption>[]>(
    (cats, cat, index) => {
      if (cat.label || index === 0) {
        return [...cats, { ...cat, items: cat.items.slice() }];
      }

      // eslint-disable-next-line no-param-reassign
      cats[index - 1].items = cats[index - 1].items.concat(cat.items);

      return cats;
    },
    [],
  );
  const noResults = inputItems.length === 0;
  const {
    getLabelProps,
    getMenuProps,
    getInputProps,
    getItemProps,
    setHighlightedIndex,
    setInputValue,
    openMenu,
  } = useCombobox<ComboBoxOption>({
    ...(typeof inputValue !== 'undefined' && { inputValue }),
    initialInputValue: inputValue || '',
    items: inputItems,
    itemToString(item: ComboBoxOption | null) {
      if (!item) {
        return '';
      }

      return getItemDescription(item) || getItemLabel(item.type, item) || '';
    },
    selectedItem: null,

    onSelectedItemChange: onSelect,

    onInputValueChange: (changes) => {
      const { inputValue: val } = changes;
      if (!val) {
        setInputItems(flatItems);
        return;
      }

      const filtered = findMatches<ComboBoxOption>(
        flatItems,
        getSearchFields,
        val,
      );
      setInputItems(filtered);
      // Always reset the first item to highlighted on filtering, to speed up selection.
      setHighlightedIndex(0);
    },
  });

  useEffect(() => {
    if (inputValue) {
      openMenu();
      setInputValue(inputValue);
      const filtered = findMatches<ComboBoxOption>(
        flatItems,
        getSearchFields,
        inputValue,
      );
      setInputItems(filtered);
      // Always reset the first item to highlighted on filtering, to speed up selection.
      setHighlightedIndex(0);
    } else {
      setInputValue('');
      setInputItems(flatItems);
      setHighlightedIndex(-1);
    }
  }, [inputValue]);

  return (
    <div className="w-combobox">
      {/* downshift does the label-field association itself. */}
      {/* eslint-disable-next-line jsx-a11y/label-has-associated-control */}
      <label {...getLabelProps()} className="w-sr-only">
        {label}
      </label>
      <div className="w-combobox__field">
        <input
          {...getInputProps()}
          type="text"
          // Prevent the field from receiving focus if it’s not visible.
          disabled={inlineCombobox}
          placeholder={placeholder}
        />
      </div>
      {noResults ? (
        <div className="w-combobox__status">{noResultsText}</div>
      ) : null}
      <div {...getMenuProps()} className="w-combobox__menu">
        {categories.map((category) => {
          const categoryItems = (category.items || []).filter((item) =>
            inputItems.find((i) => i.type === item.type),
          );
          const itemColumns = Math.ceil(categoryItems.length / 2);

          if (categoryItems.length === 0) {
            return null;
          }

          return (
            <div className="w-combobox__optgroup" key={category.type}>
              {category.label ? (
                <div className="w-combobox__optgroup-label">
                  {category.label}
                </div>
              ) : null}
              {categoryItems.map((item, index) => {
                const itemLabel = getItemLabel(item.type, item);
                const description = getItemDescription(item);
                const itemIndex = inputItems.findIndex(
                  (i) => i.type === item.type,
                );
                const itemColumn = index + 1 <= itemColumns ? 1 : 2;
                const hasIcon =
                  typeof item.icon !== 'undefined' && item.icon !== null;
                let icon: JSX.Element | null | undefined = null;

                if (hasIcon) {
                  icon =
                    typeof item.icon === 'string' ? (
                      <Icon name={item.icon} />
                    ) : (
                      item.icon
                    );
                }

                const onMouseDown = (e) => {
                  e.stopPropagation();
                  onSelect({
                    selectedItem: item,
                    type: '__item_click__' as UseComboboxStateChangeTypes.ItemClick,
                  });
                };

                return (
                  // Side-step Downshift event handling and trigger selection on mouse down for clicks,
                  // so we preserve keyboard focus when used within rich text editors.
                  // eslint-disable-next-line jsx-a11y/no-static-element-interactions
                  <div
                    key={item.type}
                    {...getItemProps({ item, index: itemIndex })}
                    onMouseDown={onMouseDown}
                    className={`w-combobox__option w-combobox__option--col${itemColumn}`}
                  >
                    <div className="w-combobox__option-icon">
                      {icon}
                      {/* Support for rich text options using text as an icon (for example "B" for bold). */}
                      {itemLabel && !hasIcon ? <span>{itemLabel}</span> : null}
                    </div>
                    <div className="w-combobox__option-text">
                      {item.render
                        ? item.render({ option: item })
                        : description}
                    </div>
                  </div>
                );
              })}
            </div>
          );
        })}
      </div>
    </div>
  );
}
