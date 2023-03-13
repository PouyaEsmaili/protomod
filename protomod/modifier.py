from io import StringIO
from typing import Tuple, List, Optional

from antlr4 import *
from ProtobufLexer import ProtobufLexer
from ProtobufParser import ProtobufParser


class ProtoModifier:
    def __init__(self,
                 include_rpc_with_option_names: Optional[List[str]] = None,
                 allowed_message_names: Optional[List[str]] = None):
        self.include_rpc_with_option_names = include_rpc_with_option_names
        self.allowed_message_names = allowed_message_names

    def get_used_message_names(self, tree: ProtobufParser.FileContext) -> List[str]:
        _, used_message_names = self.generate_file(tree)

    def regenerate_file(self, tree: ProtobufParser.FileContext) -> str:
        return self.generate_file(tree)[0]

    def parse_file(self, addr: str) -> ProtobufParser.FileContext:
        input_stream = FileStream(addr, encoding="utf-8")
        lexer = ProtobufLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = ProtobufParser(stream)
        tree = parser.file_()
        return tree

    def generate_ident(self, node: ProtobufParser.IdentContext) -> str:
        output = StringIO()
        if isinstance(node, TerminalNode):
            output.write(node.getText())
        else:
            for child in node.getChildren():
                output.write(child.getText())
        return output.getvalue()

    def generate_qualified_identifier(self, node: ProtobufParser.QualifiedIdentifierContext) -> str:
        output = StringIO()
        for child in node.getChildren():
            if isinstance(child, ProtobufParser.IdentContext):
                output.write(self.generate_ident(child))
            elif isinstance(child, TerminalNode):
                output.write(child.getText())
        return output.getvalue()

    def generate_package_name(self, node: ProtobufParser.PackageNameContext) -> str:
        output = StringIO()
        for child in node.getTypedRuleContexts(ProtobufParser.QualifiedIdentifierContext):
            output.write(self.generate_qualified_identifier(child))
        return output.getvalue()

    def generate_package_decl(self, node: ProtobufParser.PackageDeclContext) -> str:
        output = StringIO()
        for child in node.getTokens(ProtobufParser.PACKAGE):
            output.write(child.getText() + " ")
        for child in node.getTypedRuleContexts(ProtobufParser.PackageNameContext):
            output.write(self.generate_package_name(child))
        for child in node.getTokens(ProtobufParser.SEMICOLON):
            output.write(child.getText() + "\n")
        return output.getvalue()

    def generate_imported_file_name(self, node: ProtobufParser.ImportedFileNameContext) -> str:
        output = StringIO()
        for child in node.getTypedRuleContexts(ProtobufParser.StringLiteralContext):
            output.write(self.generate_string_literal(child))
        return output.getvalue()

    def generate_import_decl(self, node: ProtobufParser.ImportDeclContext) -> str:
        output = StringIO()
        for child in node.getTokens(ProtobufParser.IMPORT):
            output.write(child.getText() + " ")
        for child in node.getTokens(ProtobufParser.WEAK) + node.getTokens(ProtobufParser.PUBLIC):
            output.write(child.getText() + " ")
        for child in node.getTypedRuleContexts(ProtobufParser.ImportedFileNameContext):
            output.write(self.generate_imported_file_name(child))
        for child in node.getTokens(ProtobufParser.SEMICOLON):
            output.write(child.getText() + "\n")
        return output.getvalue()

    def generate_string_literal(self, node: ProtobufParser.StringLiteralContext) -> str:
        output = StringIO()
        for child in node.getTokens(ProtobufParser.STRING_LITERAL):
            output.write(child.getText())
        return output.getvalue()

    def generate_syntax_level(self, node: ProtobufParser.SyntaxLevelContext) -> str:
        output = StringIO()
        for child in node.getTypedRuleContexts(ProtobufParser.StringLiteralContext):
            output.write(self.generate_string_literal(child))
        return output.getvalue()

    def generate_syntax_decl(self, node: ProtobufParser.SyntaxDeclContext) -> str:
        output = StringIO()
        for child in node.getTokens(ProtobufParser.SYNTAX):
            output.write(child.getText() + " ")
        for child in node.getTokens(ProtobufParser.EQUALS):
            output.write(child.getText() + " ")
        for child in node.getTypedRuleContexts(ProtobufParser.SyntaxLevelContext):
            output.write(self.generate_syntax_level(child))
        for child in node.getTokens(ProtobufParser.SEMICOLON):
            output.write(child.getText() + "\n")
        return output.getvalue()

    def generate_option_name(self, node: ProtobufParser.OptionNameContext) -> str:
        output = StringIO()
        child = node.getChild(0)
        if isinstance(child, ProtobufParser.IdentContext):
            output.write(self.generate_ident(child))
            f = 1
        else:
            output.write(child.getText())
            child = node.getChild(1)
            output.write(child.getText())
            child = node.getChild(2)
            output.write(self.generate_ident(child))
            f = 3
        for i in range(f, node.getChildCount(), 2):
            child = node.getChild(i)
            output.write(child.getText())
            child = node.getChild(i + 1)
            output.write(self.generate_option_name(child))
        return output.getvalue()

    def generate_uint_literal(self, node: ProtobufParser.UintLiteralContext) -> str:
        output = StringIO()
        child = node.PLUS()
        if child is not None:
            output.write(child.getText())
        child = node.INT_LITERAL()
        output.write(child.getText())
        return output.getvalue()

    def generate_int_literal(self, node: ProtobufParser.IntLiteralContext) -> str:
        output = StringIO()
        child = node.MINUS()
        if child is not None:
            output.write(child.getText())
        child = node.INT_LITERAL()
        output.write(child.getText())
        return output.getvalue()

    def generate_float_literal(self, node: ProtobufParser.FloatLiteralContext) -> str:
        output = StringIO()
        child = node.MINUS()
        if child is not None:
            output.write(child.getText())
        child = node.PLUS()
        if child is not None:
            output.write(child.getText())
        child = node.FLOAT_LITERAL()
        if child is not None:
            output.write(child.getText())
        child = node.INF()
        if child is not None:
            output.write(child.getText())
        return output.getvalue()

    def generate_scalar_value(self, node: ProtobufParser.ScalarValueContext) -> str:
        output = StringIO()
        child = node.getChild(0)
        if isinstance(child, ProtobufParser.StringLiteralContext):
            output.write(self.generate_string_literal(child))
        elif isinstance(child, ProtobufParser.UintLiteralContext):
            output.write(self.generate_uint_literal(child))
        elif isinstance(child, ProtobufParser.IntLiteralContext):
            output.write(self.generate_int_literal(child))
        elif isinstance(child, ProtobufParser.FloatLiteralContext):
            output.write(self.generate_float_literal(child))
        elif isinstance(child, ProtobufParser.IdentContext):
            output.write(self.generate_ident(child))
        return output.getvalue()

    def generate_extension_field_name(self, node: ProtobufParser.ExtensionFieldNameContext) -> str:
        output = StringIO()
        child = node.qualifiedIdentifier()
        output.write(self.generate_qualified_identifier(child))
        return output.getvalue()

    def generate_type_url(self, node: ProtobufParser.TypeURLContext) -> str:
        output = StringIO()
        child = node.getChild(0)
        output.write(self.generate_qualified_identifier(child))
        child = node.SLASH()
        output.write(child.getText())
        child = node.getChild(2)
        output.write(self.generate_qualified_identifier(child))
        return output.getvalue()

    def generate_special_field_name(self, node: ProtobufParser.SpecialFieldNameContext) -> str:
        output = StringIO()
        child = node.extensionFieldName()
        if child is not None:
            output.write(self.generate_extension_field_name(child))
        child = node.typeURL()
        if child is not None:
            output.write(self.generate_type_url(child))
        return output.getvalue()

    def generate_message_literal_field_name(self, node: ProtobufParser.MessageLiteralFieldNameContext) -> str:
        output = StringIO()
        child = node.getChild(0)
        if isinstance(child, ProtobufParser.FieldNameContext):
            output.write(self.generate_field_name(child))
        else:
            output.write(child.getText())
            child = node.getChild(1)
            output.write(self.generate_special_field_name(child))
            child = node.getChild(2)
            output.write(child.getText())
        return output.getvalue()

    def generate_message_literal(self, node: ProtobufParser.MessageLiteralContext) -> str:
        output = StringIO()
        child = node.getChild(0)
        if isinstance(child, ProtobufParser.MessageLiteralWithBracesContext):
            output.write(self.generate_message_literal_with_braces(child))
        else:
            output.write(child.getText())
            child = node.getChild(1)
            output.write(self.generate_message_text_format(child))
            child = node.getChild(2)
            output.write(child.getText())
        return output.getvalue()

    def generate_list_element(self, node: ProtobufParser.ListElementContext, indent=0) -> str:
        output = StringIO()
        output.write(" " * indent * 2)
        child = node.scalarValue()
        if child is not None:
            output.write(self.generate_scalar_value(child))
        child = node.messageLiteral()
        if child is not None:
            output.write(self.generate_message_literal(child))
        return output.getvalue()

    def generate_list_literal(self, node: ProtobufParser.ListLiteralContext, indent=0) -> str:
        output = StringIO()
        for child in node.getChildren():
            if isinstance(child, TerminalNode):
                if child.getText() == "]":
                    output.write("\n" + " " * indent * 2 + child.getText())
                else:
                    output.write(child.getText() + "\n")
            elif isinstance(child, ProtobufParser.ListElementContext):
                output.write(self.generate_list_element(child, indent + 1))
        return output.getvalue()

    def generate_value(self, node: ProtobufParser.ValueContext, indent=0) -> str:
        output = StringIO()
        child = node.scalarValue()
        if child is not None:
            output.write(self.generate_scalar_value(child))
        child = node.messageLiteral()
        if child is not None:
            output.write(self.generate_message_literal(child))
        child = node.listLiteral()
        if child is not None:
            output.write(self.generate_list_literal(child, indent))
        return output.getvalue()

    def generate_list_of_messages_literal(self, node: ProtobufParser.ListOfMessagesLiteralContext) -> str:
        output = StringIO()
        for child in node.getChildren():
            if isinstance(child, TerminalNode):
                if child.getText() == ",":
                    output.write(child.getText() + " ")
                else:
                    output.write(child.getText())
            elif isinstance(child, ProtobufParser.MessageLiteralContext):
                output.write(self.generate_message_literal(child))
            else:
                "!!Error!!"
        return output.getvalue()

    def generate_message_value(self, node: ProtobufParser.MessageValueContext) -> str:
        output = StringIO()
        child = node.getChild(0)
        if isinstance(child, ProtobufParser.MessageLiteralContext):
            output.write(self.generate_message_literal(child))
        elif isinstance(child, ProtobufParser.ListOfMessagesLiteralContext):
            output.write(self.generate_list_of_messages_literal(child))
        return output.getvalue()

    def generate_message_literal_field(self, node: ProtobufParser.MessageLiteralFieldContext, ident) -> str:
        output = StringIO()
        child = node.messageLiteralFieldName()
        output.write(self.generate_message_literal_field_name(child))
        child = node.getChild(1)
        if isinstance(child, TerminalNode):
            output.write(child.getText() + " ")
            child = node.getChild(2)
            output.write(self.generate_value(child, ident))
        else:
            output.write(self.generate_message_value(child))
        return output.getvalue()

    def generate_message_text_format(self, node: ProtobufParser.MessageTextFormatContext, indent=0) -> str:
        output = StringIO()
        for child in node.getChildren():
            if isinstance(child, ProtobufParser.MessageLiteralFieldContext):
                output.write(" " * indent * 2)
                output.write(self.generate_message_literal_field(child, indent))
            elif isinstance(child, TerminalNode):
                if child.getText() == ";":
                    output.write(child.getText() + "\n")
                else:
                    output.write(child.getText() + " ")
            else:
                output.write("!!Error!!")
            output.write("\n")
        return output.getvalue()[0:-1]

    def generate_message_literal_with_braces(self, node: ProtobufParser.MessageLiteralWithBracesContext,
                                             indent=0) -> str:
        output = StringIO()
        child = node.L_BRACE()
        output.write(child.getText() + "\n")
        child = node.messageTextFormat()
        output.write(self.generate_message_text_format(child, indent + 1) + "\n")
        child = node.R_BRACE()
        output.write(" " * indent * 2 + child.getText())
        return output.getvalue()

    def generate_option_value(self, node: ProtobufParser.OptionValueContext, indent=0) -> str:
        output = StringIO()
        for child in node.getChildren():
            if isinstance(child, ProtobufParser.ScalarValueContext):
                output.write(self.generate_scalar_value(child))
            if isinstance(child, ProtobufParser.MessageLiteralWithBracesContext):
                output.write(self.generate_message_literal_with_braces(child, indent))
        return output.getvalue()

    def generate_option_decl(self, node: ProtobufParser.OptionDeclContext, indent=0) -> Tuple[str, bool]:
        should_render_this = False
        output = StringIO()
        child = node.OPTION()
        output.write(child.getText() + " ")
        child = node.optionName()
        option_name = self.generate_option_name(child)
        if not self.include_rpc_with_option_names or option_name[1:-1] in self.include_rpc_with_option_names:
            should_render_this = True
        output.write(option_name + " ")
        child = node.EQUALS()
        output.write(child.getText() + " ")
        child = node.optionValue()
        output.write(self.generate_option_value(child, indent))
        child = node.SEMICOLON()
        output.write(child.getText() + "\n")
        return output.getvalue(), should_render_this

    def generate_message_name(self, node: ProtobufParser.MessageNameContext) -> str:
        output = StringIO()
        child = node.ident()
        output.write(self.generate_ident(child))
        return output.getvalue()

    def generate_field_cardinality(self, node: ProtobufParser.FieldCardinalityContext) -> str:
        output = StringIO()
        child = node.getChild(0)
        output.write(child.getText())
        return output.getvalue()

    def generate_type_name(self, node: ProtobufParser.TypeNameContext) -> str:
        output = StringIO()
        child = node.DOT()
        if child is not None:
            output.write(child.getText())
        child = node.qualifiedIdentifier()
        output.write(self.generate_qualified_identifier(child))
        return output.getvalue()

    def generate_field_name(self, node: ProtobufParser.FieldNameContext) -> str:
        output = StringIO()
        child = node.ident()
        output.write(self.generate_ident(child))
        return output.getvalue()

    def generate_field_number(self, node: ProtobufParser.FieldNumberContext) -> str:
        output = StringIO()
        child = node.INT_LITERAL()
        output.write(child.getText())
        return output.getvalue()

    def generate_compact_option(self, node: ProtobufParser.CompactOptionContext) -> str:
        output = StringIO()
        child = node.optionName()
        output.write(self.generate_option_name(child) + " ")
        child = node.EQUALS()
        output.write(child.getText() + " ")
        child = node.optionValue()
        output.write(self.generate_option_value(child))
        return output.getvalue()

    def generate_compact_options(self, node: ProtobufParser.CompactOptionsContext) -> str:
        output = StringIO()
        for child in node.getChildren():
            if isinstance(child, ProtobufParser.CompactOptionContext):
                output.write(self.generate_compact_option(child))
            elif isinstance(child, TerminalNode):
                if child.getText() == ",":
                    output.write(child.getText() + " ")
                elif child.getText() == "[":
                    output.write(child.getText() + " ")
                elif child.getText() == "]":
                    output.write(child.getText())
        return output.getvalue()

    def generate_enum_name(self, node: ProtobufParser.EnumNameContext) -> str:
        output = StringIO()
        child = node.ident()
        output.write(self.generate_ident(child))
        return output.getvalue()

    def generate_enum_value_name(self, node: ProtobufParser.EnumValueNameContext) -> str:
        output = StringIO()
        child = node.ident()
        output.write(self.generate_ident(child))
        return output.getvalue()

    def generate_enum_value_number(self, node: ProtobufParser.EnumValueNumberContext) -> str:
        output = StringIO()
        child = node.MINUS()
        if child is not None:
            output.write(child.getText())
        child = node.INT_LITERAL()
        output.write(child.getText())
        return output.getvalue()

    def generate_enum_value_decl(self, node: ProtobufParser.EnumValueDeclContext) -> str:
        output = StringIO()
        child = node.enumValueName()
        output.write(self.generate_enum_value_name(child) + " ")
        child = node.EQUALS()
        output.write(child.getText() + " ")
        child = node.enumValueNumber()
        output.write(self.generate_enum_value_number(child))
        child = node.compactOptions()
        if child is not None:
            output.write(self.generate_compact_options(child))
        child = node.SEMICOLON()
        output.write(child.getText() + "\n")
        return output.getvalue()

    def generate_enum_value_range_start(self, node: ProtobufParser.EnumValueRangeStartContext) -> str:
        output = StringIO()
        child = node.enumValueNumber()
        output.write(self.generate_enum_value_number(child))
        return output.getvalue()

    def generate_enum_value_range_end(self, node: ProtobufParser.EnumValueRangeEndContext) -> str:
        output = StringIO()
        child = node.enumValueNumber()
        if child is not None:
            output.write(self.generate_enum_value_number(child))
        child = node.MAX()
        if child is not None:
            output.write(child.getText())
        return output.getvalue()

    def generate_enum_value_range(self, node: ProtobufParser.EnumValueRangeContext) -> str:
        output = StringIO()
        child = node.enumValueRangeStart()
        output.write(self.generate_enum_value_range_start(child) + " ")
        child = node.TO()
        if child is not None:
            output.write(" " + child.getText() + " ")
            child = node.enumValueRangeEnd()
            output.write(self.generate_enum_value_range_end(child))
        return output.getvalue()

    def generate_enum_value_ranges(self, node: ProtobufParser.EnumValueRangesContext) -> str:
        output = StringIO()
        for child in node.getChildren():
            if isinstance(child, ProtobufParser.EnumValueRangeContext):
                output.write(self.generate_enum_value_range(child))
            elif isinstance(child, TerminalNode):
                output.write(child.getText() + " ")
        return output.getvalue()

    def generate_enum_reserved_decl(self, node: ProtobufParser.EnumReservedDeclContext) -> str:
        output = StringIO()
        child = node.RESERVED()
        output.write(child.getText() + " ")
        child = node.enumValueRanges()
        if child is not None:
            output.write(self.generate_enum_value_ranges(child))
        child = node.names()
        if child is not None:
            output.write(self.generate_names(child))
        child = node.SEMICOLON()
        output.write(child.getText() + "\n")
        return output.getvalue()

    def generate_empty_decl(self, node: ProtobufParser.EmptyDeclContext) -> str:
        output = StringIO()
        child = node.SEMICOLON()
        output.write(child.getText() + "\n")
        return output.getvalue()

    def generate_enum_element(self, node: ProtobufParser.EnumElementContext, indent=0) -> str:
        output = StringIO()
        output.write(" " * indent * 2)
        child = node.optionDecl()
        if child is not None:
            output.write(self.generate_option_decl(child))
        child = node.enumValueDecl()
        if child is not None:
            output.write(self.generate_enum_value_decl(child))
        child = node.enumReservedDecl()
        if child is not None:
            output.write(self.generate_enum_reserved_decl(child))
        child = node.emptyDecl()
        if child is not None:
            output.write(self.generate_empty_decl(child))
        return output.getvalue()

    def generate_oneof_name(self, node: ProtobufParser.OneofNameContext) -> str:
        output = StringIO()
        child = node.ident()
        output.write(self.generate_ident(child))
        return output.getvalue()

    def generate_oneof_field_decl(self, node: ProtobufParser.OneofFieldDeclContext) -> str:
        output = StringIO()
        child = node.typeName()
        output.write(self.generate_type_name(child) + " ")
        child = node.fieldName()
        output.write(self.generate_field_name(child) + " ")
        child = node.EQUALS()
        output.write(child.getText() + " ")
        child = node.fieldNumber()
        output.write(self.generate_field_number(child))
        child = node.compactOptions()
        if child is not None:
            output.write(self.generate_compact_options(child))
        child = node.SEMICOLON()
        output.write(child.getText() + "\n")
        return output.getvalue()

    def generate_oneof_group_decl(self, node: ProtobufParser.OneofGroupDeclContext, indent=0) -> str:
        output = StringIO()
        child = node.GROUP()
        output.write(child.getText() + " ")
        child = node.fieldName()
        output.write(self.generate_field_name(child) + " ")
        child = node.EQUALS()
        output.write(child.getText() + " ")
        child = node.fieldNumber()
        output.write(self.generate_field_number(child))
        child = node.compactOptions()
        if child is not None:
            output.write(self.generate_compact_options(child) + " ")
        child = node.L_BRACE()
        output.write(" " * indent * 2 + child.getText() + "\n")
        for child in node.getTypedRuleContexts(ProtobufParser.MessageElementContext):
            output.write(self.generate_message_element(child, indent + 1))
        child = node.R_BRACE()
        output.write(" " * indent * 2 + child.getText() + "\n")
        return output.getvalue()

    def generate_oneof_element(self, node: ProtobufParser.OneofElementContext, indent=0) -> str:
        output = StringIO()
        output.write(" " * indent * 2)
        child = node.optionDecl()
        if child is not None:
            output.write(self.generate_option_decl(child))
        child = node.oneofFieldDecl()
        if child is not None:
            output.write(self.generate_oneof_field_decl(child))
        child = node.oneofGroupDecl()
        if child is not None:
            output.write(self.generate_oneof_group_decl(child, indent + 1))
        return output.getvalue()

    def generate_map_key_type(self, node: ProtobufParser.MapKeyTypeContext) -> str:
        output = StringIO()
        child = node.getChild(0)
        output.write(child.getText())
        return output.getvalue()

    def generate_map_type(self, node: ProtobufParser.MapTypeContext) -> str:
        output = StringIO()
        child = node.MAP()
        output.write(child.getText())
        child = node.L_ANGLE()
        output.write(child.getText())
        child = node.mapKeyType()
        output.write(self.generate_map_key_type(child))
        child = node.COMMA()
        output.write(child.getText() + " ")
        child = node.typeName()
        output.write(self.generate_type_name(child))
        child = node.R_ANGLE()
        output.write(child.getText())
        return output.getvalue()

    def generate_service_name(self, node: ProtobufParser.ServiceNameContext) -> str:
        output = StringIO()
        child = node.ident()
        output.write(self.generate_ident(child))
        return output.getvalue()

    def generate_method_name(self, node: ProtobufParser.MethodNameContext) -> str:
        output = StringIO()
        child = node.ident()
        output.write(self.generate_ident(child))
        return output.getvalue()

    def generate_message_type(self, node: ProtobufParser.MessageTypeContext) -> Tuple[str, str]:
        output = StringIO()
        child = node.L_PAREN()
        output.write(child.getText())
        child = node.STREAM()
        if child is not None:
            output.write(child.getText() + " ")
        child = node.typeName()
        type_name = self.generate_type_name(child)
        output.write(type_name)
        child = node.R_PAREN()
        output.write(child.getText())
        return output.getvalue(), type_name

    def generate_input_type(self, node: ProtobufParser.InputTypeContext) -> Tuple[str, str]:
        output = StringIO()
        child = node.messageType()
        message_type, message_name = self.generate_message_type(child)
        output.write(message_type)
        return output.getvalue(), message_name

    def generate_output_type(self, node: ProtobufParser.OutputTypeContext) -> Tuple[str, str]:
        output = StringIO()
        child = node.messageType()
        message_type, message_name = self.generate_message_type(child)
        output.write(message_type)
        return output.getvalue(), message_name

    def generate_field_decl(self, node: ProtobufParser.FieldDeclContext) -> str:
        output = StringIO()
        child = node.fieldCardinality()
        if child is not None:
            output.write(self.generate_field_cardinality(child) + " ")
        child = node.typeName()
        output.write(self.generate_type_name(child) + " ")
        child = node.fieldName()
        output.write(self.generate_field_name(child) + " ")
        child = node.EQUALS()
        output.write(child.getText() + " ")
        child = node.fieldNumber()
        output.write(self.generate_field_number(child))
        child = node.compactOptions()
        if child is not None:
            output.write(" " + self.generate_compact_options(child))
        child = node.SEMICOLON()
        output.write(child.getText() + "\n")
        return output.getvalue()

    def generate_group_decl(self, node: ProtobufParser.GroupDeclContext, indent=0) -> str:
        output = StringIO()
        child = node.fieldCardinality()
        if child is not None:
            output.write(self.generate_field_cardinality(child) + " ")
        child = node.GROUP()
        output.write(child.getText() + " ")
        child = node.fieldName()
        output.write(self.generate_field_name(child) + " ")
        child = node.EQUALS()
        output.write(child.getText() + " ")
        child = node.fieldNumber()
        output.write(self.generate_field_number(child))
        child = node.compactOptions()
        if child is not None:
            output.write(" " + self.generate_compact_options(child))
        child = node.L_BRACE()
        output.write(" " * indent * 2 + child.getText() + "\n")
        for child in node.getTypedRuleContexts(ProtobufParser.MessageElementContext):
            output.write(self.generate_message_element(child, indent + 1))
        child = node.R_BRACE()
        output.write(" " * indent * 2 + child.getText() + "\n")
        return output.getvalue()

    def generate_oneof_decl(self, node: ProtobufParser.OneofDeclContext, indent=0) -> str:
        output = StringIO()
        child = node.ONEOF()
        output.write(child.getText() + " ")
        child = node.oneofName()
        output.write(self.generate_oneof_name(child) + " ")
        child = node.L_BRACE()
        output.write(child.getText() + "\n")
        for child in node.getTypedRuleContexts(ProtobufParser.OneofElementContext):
            output.write(self.generate_oneof_element(child, indent + 1))
        child = node.R_BRACE()
        output.write(" " * indent * 2 + child.getText() + "\n")
        return output.getvalue()

    def generate_extension_range_decl(self, node: ProtobufParser.ExtensionRangeDeclContext) -> str:
        output = StringIO()
        child = node.EXTENSIONS()
        output.write(child.getText() + " ")
        child = node.tagRanges()
        output.write(self.generate_tag_ranges(child))
        child = node.compactOptions()
        if child is not None:
            output.write(" " + self.generate_compact_options(child))
        child = node.SEMICOLON()
        output.write(child.getText() + "\n")
        return output.getvalue()

    def generate_tag_range_start(self, node: ProtobufParser.TagRangeStartContext) -> str:
        output = StringIO()
        child = node.fieldNumber()
        output.write(self.generate_field_number(child))
        return output.getvalue()

    def generate_tag_range_end(self, node: ProtobufParser.TagRangeEndContext) -> str:
        output = StringIO()
        child = node.fieldNumber()
        if child is not None:
            output.write(self.generate_field_number(child))
        child = node.MAX()
        if child is not None:
            output.write(child.getText())
        return output.getvalue()

    def generate_tag_range(self, node: ProtobufParser.TagRangeContext) -> str:
        output = StringIO()
        child = node.tagRangeStart()
        output.write(self.generate_tag_range_start(child))
        child = node.TO()
        if child is not None:
            output.write(" " + child.getText() + " ")
            child = node.tagRangeEnd()
            output.write(self.generate_tag_range_end(child))
        return output.getvalue()

    def generate_tag_ranges(self, node: ProtobufParser.TagRangesContext) -> str:
        output = StringIO()
        for child in node.getChildren():
            if isinstance(child, TerminalNode):
                output.write(child.getText() + " ")
            elif isinstance(child, ProtobufParser.TagRangeContext):
                output.write(self.generate_tag_range(child))
        return output.getvalue()

    def generate_names(self, node: ProtobufParser.NamesContext) -> str:
        output = StringIO()
        for child in node.getChildren():
            if isinstance(child, TerminalNode):
                output.write(child.getText() + " ")
            elif isinstance(child, ProtobufParser.StringLiteralContext):
                output.write(self.generate_string_literal(child))
        return output.getvalue()

    def generate_extended_message(self, node: ProtobufParser.ExtendedMessageContext):
        output = StringIO()
        child = node.typeName()
        output.write(self.generate_type_name(child))
        return output.getvalue()

    def generate_extension_element(self, node: ProtobufParser.ExtensionElementContext, indent=0):
        output = StringIO()
        output.write(" " * indent * 2)
        child = node.fieldDecl()
        if child is not None:
            output.write(self.generate_field_decl(child))
        child = node.groupDecl()
        if child is not None:
            output.write(self.generate_group_decl(child))
        return output.getvalue()

    def generate_message_reserved_decl(self, node: ProtobufParser.MessageReservedDeclContext) -> str:
        output = StringIO()
        child = node.RESERVED()
        output.write(child.getText() + " ")
        child = node.tagRanges()
        if child is not None:
            output.write(self.generate_tag_ranges(child))
        child = node.names()
        if child is not None:
            output.write(self.generate_names(child))
        child = node.SEMICOLON()
        output.write(child.getText() + "\n")
        return output.getvalue()

    def generate_enum_decl(self, node: ProtobufParser.EnumDeclContext, indent=0) -> str:
        output = StringIO()
        output.write(" " * indent * 2)
        child = node.ENUM()
        output.write(child.getText() + " ")
        child = node.enumName()
        output.write(self.generate_enum_name(child) + " ")
        child = node.L_BRACE()
        output.write(child.getText() + "\n")
        for child in node.getTypedRuleContexts(ProtobufParser.EnumElementContext):
            output.write(self.generate_enum_element(child, indent + 1))
        child = node.R_BRACE()
        output.write(" " * indent * 2 + child.getText() + "\n")
        return output.getvalue()

    def generate_extension_decl(self, node: ProtobufParser.ExtensionDeclContext, indent=0) -> str:
        output = StringIO()
        child = node.EXTEND()
        output.write(child.getText() + " ")
        child = node.extendedMessage()
        output.write(self.generate_extended_message(child) + " ")
        child = node.L_BRACE()
        output.write(child.getText() + "\n")
        for child in node.getTypedRuleContexts(ProtobufParser.ExtensionElementContext):
            output.write(self.generate_extension_element(child, indent + 1))
        child = node.R_BRACE()
        output.write(" " * indent * 2 + child.getText() + "\n")
        return output.getvalue()

    def generate_map_field_decl(self, node: ProtobufParser.MapFieldDeclContext) -> str:
        output = StringIO()
        child = node.mapType()
        output.write(self.generate_map_type(child) + " ")
        child = node.fieldName()
        output.write(self.generate_field_name(child) + " ")
        child = node.EQUALS()
        output.write(child.getText() + " ")
        child = node.fieldNumber()
        output.write(self.generate_field_number(child))
        child = node.compactOptions()
        if child is not None:
            output.write(" " + self.generate_compact_options(child))
        child = node.SEMICOLON()
        output.write(child.getText() + "\n")
        return output.getvalue()

    def generate_message_element(self, node: ProtobufParser.MessageElementContext, indent=0) -> str:
        output = StringIO()
        output.write(" " * indent * 2)
        for child in node.getChildren():
            if isinstance(child, ProtobufParser.FieldDeclContext):
                output.write(self.generate_field_decl(child))
            elif isinstance(child, ProtobufParser.GroupDeclContext):
                output.write(self.generate_group_decl(child))
            elif isinstance(child, ProtobufParser.OneofDeclContext):
                output.write(self.generate_oneof_decl(child, indent))
            elif isinstance(child, ProtobufParser.OptionDeclContext):
                output.write(self.generate_option_decl(child)[0])
            elif isinstance(child, ProtobufParser.ExtensionRangeDeclContext):
                output.write(self.generate_extension_range_decl(child))
            elif isinstance(child, ProtobufParser.MessageReservedDeclContext):
                output.write(self.generate_message_reserved_decl(child))
            elif isinstance(child, ProtobufParser.MessageDeclContext):
                output.write(self.generate_message_decl(child, indent)[0])
            elif isinstance(child, ProtobufParser.EnumDeclContext):
                output.write(self.generate_enum_decl(child))
            elif isinstance(child, ProtobufParser.ExtensionDeclContext):
                output.write(self.generate_extension_decl(child, indent))
            elif isinstance(child, ProtobufParser.MapFieldDeclContext):
                output.write(self.generate_map_field_decl(child))
            elif isinstance(child, ProtobufParser.EmptyDeclContext):
                output.write(self.generate_empty_decl(child))
        return output.getvalue()

    def generate_message_decl(self, node: ProtobufParser.MessageDeclContext, indent=0) -> Tuple[str, bool]:
        should_render_this = True
        output = StringIO()
        child = node.MESSAGE()
        output.write(child.getText() + " ")
        child = node.messageName()
        message_name = self.generate_message_name(child)
        output.write(message_name + " ")
        should_render_this = should_render_this or message_name in self.allowed_message_names
        child = node.L_BRACE()
        output.write(child.getText() + "\n")
        for child in node.getTypedRuleContexts(ProtobufParser.MessageElementContext):
            output.write(self.generate_message_element(child, indent + 1))
        child = node.R_BRACE()
        output.write(" " * indent * 2 + child.getText() + "\n")
        return output.getvalue(), should_render_this

    def generate_method_element(self, node: ProtobufParser.MethodElementContext, indent=0) -> Tuple[str, bool]:
        should_render_this = False
        output = StringIO()
        output.write(" " * indent * 2)
        child = node.optionDecl()
        if child is not None:
            res, should_render = self.generate_option_decl(child, indent)
            should_render_this = should_render_this or should_render
            output.write(res)
        child = node.emptyDecl()
        if child is not None:
            output.write(self.generate_empty_decl(child))
        return output.getvalue(), should_render_this

    def generate_method_decl(self, node: ProtobufParser.MethodDeclContext, indent=0) -> Tuple[str, bool, List[str]]:
        should_render_this = False
        message_names = []
        output = StringIO()
        child = node.RPC()
        output.write(child.getText() + " ")
        child = node.methodName()
        output.write(self.generate_method_name(child))
        child = node.inputType()
        input_type, message_name = self.generate_input_type(child)
        message_names.append(message_name)
        output.write(input_type + " ")
        child = node.RETURNS()
        output.write(child.getText() + " ")
        child = node.outputType()
        output_type, message_name = self.generate_output_type(child)
        message_names.append(message_name)
        output.write(output_type)
        child = node.SEMICOLON()
        if child is not None:
            output.write(child.getText() + "\n")
        else:
            child = node.L_BRACE()
            output.write(child.getText() + ("\n" if node.methodElement() else ""))
            for child in node.getTypedRuleContexts(ProtobufParser.MethodElementContext):
                res, should_render = self.generate_method_element(child, indent + 1)
                should_render_this = should_render or should_render_this
                output.write(res)
            child = node.R_BRACE()
            output.write(" " * indent * 2 + child.getText() + "\n")
        return output.getvalue(), should_render_this, message_names

    def generate_service_element(self, node: ProtobufParser.ServiceElementContext, indent=0) -> Tuple[
        str, bool, List[str]]:
        should_render_this = False
        message_names = []
        output = StringIO()
        output.write(" " * indent * 2)
        child = node.optionDecl()
        if child is not None:
            output.write(self.generate_option_decl(child)[0])
        child = node.methodDecl()
        if child is not None:
            res, should_render, message_names = self.generate_method_decl(child, indent)
            should_render_this = should_render or should_render_this
            output.write(res if should_render else "")
        child = node.emptyDecl()
        if child is not None:
            output.write(self.generate_empty_decl(child))
        return output.getvalue(), should_render_this, message_names

    def generate_service_decl(self, node: ProtobufParser.ServiceDeclContext, indent=0) -> Tuple[str, bool, List[str]]:
        should_render_this = False
        message_names = []
        output = StringIO()
        output.write(" " * indent * 2)
        child = node.SERVICE()
        output.write(child.getText() + " ")
        child = node.serviceName()
        output.write(self.generate_service_name(child) + " ")
        child = node.L_BRACE()
        output.write(child.getText() + "\n")
        for child in node.getTypedRuleContexts(ProtobufParser.ServiceElementContext):
            res, should_render, _message_names = self.generate_service_element(child, indent + 1)
            message_names += _message_names
            should_render_this = should_render or should_render_this
            output.write(res if should_render else "")
        child = node.R_BRACE()
        output.write(" " * indent * 2 + child.getText() + "\n")
        return output.getvalue(), should_render_this, message_names

    def generate_file_element(self, node: ProtobufParser.FileElementContext) -> Tuple[str, List[str]]:
        message_names = []
        output = StringIO()
        for child in node.getChildren():
            if isinstance(child, ProtobufParser.ImportDeclContext):
                output.write(self.generate_import_decl(child))
            elif isinstance(child, ProtobufParser.PackageDeclContext):
                output.write(self.generate_package_decl(child))
            elif isinstance(child, ProtobufParser.OptionDeclContext):
                output.write(self.generate_option_decl(child)[0])
            elif isinstance(child, ProtobufParser.MessageDeclContext):
                res, should_render = self.generate_message_decl(child)
                output.write(res if should_render else "")
            elif isinstance(child, ProtobufParser.EnumDeclContext):
                output.write(self.generate_enum_decl(child))
            elif isinstance(child, ProtobufParser.ExtensionDeclContext):
                output.write(self.generate_extension_decl(child))
            elif isinstance(child, ProtobufParser.ServiceDeclContext):
                res, should_render, message_names = self.generate_service_decl(child)
                output.write(res)
            elif isinstance(child, ProtobufParser.EmptyDeclContext):
                output.write(self.generate_empty_decl(child))
            else:
                output.write("!!Error!!")
        return output.getvalue(), message_names

    def generate_file(self, node: ProtobufParser.FileContext) -> Tuple[str, List[str]]:
        message_names = []
        output = StringIO()
        for child in node.getTokens(ProtobufParser.BYTE_ORDER_MARK):
            output.write(child.getText())
        for child in node.getTypedRuleContexts(ProtobufParser.SyntaxDeclContext):
            output.write(self.generate_syntax_decl(child))
        for child in node.getTypedRuleContexts(ProtobufParser.FileElementContext):
            res, message_names = self.generate_file_element(child)
            output.write(res)
        return output.getvalue(), message_names
